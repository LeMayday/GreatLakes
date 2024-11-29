# adapted from: https://github.com/johannesuhl/netcdf2mp4/blob/main/netcdf2mp4.py

# module load python
# pip install matplotlib netcdf4 imageio opencv-python

import os
from matplotlib import pyplot as plt
import netCDF4
import imageio.v2 as imageio
import cv2

################################# USER INPUTS #################################

# netcdf file directory
nc_dir = './bin'

frame_duration = 0.1 # seconds per frame

###############################################################################

# output files numbered 000 thru 200
filenums = range(201)
# add leading zeros
filenums = [str(item).zfill(3) for item in filenums]
# variables of interest
variables = ['rho', 'press', 'vel1', 'vel2', 'r0', 'vapor1']
units = ['kg/m^3', 'Pa', 'm/s', 'm/s', '', ''] # r0 and vapor1 are ratios

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

for var in variables:
    output_gif = './geyser_%s.gif' %var # output gif file
    output_mp4 = './geyser_%s.mp4' %var # output mp4 file
    filenames = []
    for num in filenums:
        file = '%s/geyser.out2.00%s.nc' %(nc_dir, num)
        nc_file = netCDF4.Dataset(file)

        fig,ax=plt.subplots(figsize=(4.5,6)) # adjust image aspect to your data
        img=ax.imshow(nc_file[var][0,:,:,0], cmap='jet', origin='lower')
        cbar = fig.colorbar(img)
        ax.set_title(var + ' (' + units[variables.index(var)] + ')')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

        file = '%s_%s.png' %(var, num)
        fig.tight_layout(pad=0.4)
        # save to temp png file
        fig.savefig(file)
        plt.close()
        filenames.append(file)

    '''
    # write to gif
    with imageio.get_writer(output_gif, mode='I', duration=frame_duration) as writer:
        for file in filenames:
            if os.path.exists(file):
                image = imageio.imread(file)
                writer.append_data(image)
    '''

    # write to mp4
    # https://stackoverflow.com/questions/44947505/how-to-make-a-movie-out-of-images-in-python
    frame = cv2.imread(filenames[0])
    height, width, layers = frame.shape
    video = cv2.VideoWriter(output_mp4, fourcc, 1/frame_duration, (width,height))
    for image in filenames:
        video.write(cv2.imread(image))
    cv2.destroyAllWindows()
    video.release()

    # delete temp png files
    for file in set(filenames):
        if os.path.exists(file):
            os.remove(file)
