# adapted from: https://github.com/johannesuhl/netcdf2mp4/blob/main/netcdf2mp4.py

# module load python
# pip install matplotlib netcdf4 imageio opencv-python

import os
from matplotlib import pyplot as plt
import netCDF4
import imageio.v2 as imageio
import cv2

################################# USER INPUTS #################################

nc_dir = '../bin'           # netcdf file directory
frame_duration = 0.1        # seconds per frame
num_steady_state = 120

###############################################################################

# output files numbered 000 thru 200
filenums = range(201)
# add leading zeros
filenums = [str(item).zfill(3) for item in filenums]
# variables of interest (2 or 3 corresponds to out2 or out3)
variables2 = ['rho', 'press', 'vel1', 'vel2', 'r0', 'vapor1']
units2 = ['kg/m^3', 'Pa', 'm/s', 'm/s', '', ''] # r0 and vapor1 are ratios
variables3 = ['temp', 'h2o', 'h2oc', 'co2', 'co2c']
units3 = ['K', '', '', '', '']
fourcc = cv2.VideoWriter_fourcc(*'mp4v') # mp4 codec
variables = variables2 + variables3
units = units2 + units3

###############################################################################

def main():
    ### create movies for all variables ###
    # for var in variables:
    #     output_mp4 = './geyser_%s.mp4' %var # output mp4 file
    #     if var == 'temp':
    #         create_movie(var, output_mp4, min=220, max=340)
    #     else:
    #         create_movie(var, output_mp4)

    # ### create movie for vapor1 with limited bounds to show evaporation from ice ###
    # var = 'vapor1'
    # output_mp4 = './geyser_%s_narrow_range.mp4' %var # output mp4 file
    # create_movie(var, output_mp4, min=0.64, max=0.72)

    # ### save images for certain variables in steady state ###
    # choose right file depending on variable
    variables_static = ['rho', 'vel1', 'h2o', 'h2oc', 'temp']

    for var in variables_static:
        fig = plot_var(nc_file=get_nc_file(var, num_steady_state), var=var)
        output_file = '%s_%s.png' %(var, num_steady_state)
        save_fig(fig, output_file)

    ### calculate geyser mdot at bottom and at surface ###
    nc_file = get_nc_file2(num_steady_state)
    vars = ['rho', 'vel1']
    avgs = []
    for var in vars:
        data = nc_file[var]
        # bottom of geyser is taken to be at 5 to avoid the large values at the very bottom (assumed mdot is conserved over small distance)
        bottom = data[0, 5, 41:59, 0]
        # surface is at 100 as prescribed by input file
        surface = data[0, 100, 41:59, 0]
        # take average of values across channel
        bottom_bar = avg(bottom)
        surface_bar = avg(surface)
        avgs.append([bottom_bar, surface_bar])

        # show where averages are being taken on plots
        fig = plot_var(nc_file, var)
        ax = fig.get_axes()[0]
        x_range = range(41, 59, 1)
        ax.plot(x_range, [5]*len(x_range), 'k-', linewidth=3)
        ax.plot(x_range, [100]*len(x_range), 'k-', linewidth=3)

        output_file = '%s_%s_annotated.png' %(var, num_steady_state)
        save_fig(fig, output_file)

    mdot_bottom = avgs[0][0] * avgs[1][0]
    mdot_surface = avgs[0][1] * avgs[1][1]

    # calculate ratio of mdots (paper suggests about 50% loss)
    mdot_ratio = mdot_surface / mdot_bottom
    print(mdot_ratio)

###############################################################################

def avg(l):
    return sum(l) / len(l)

# plots variable and returns matplotlib figure
def plot_var(nc_file, var, min=None, max=None):
    # plot image
    fig,ax = plt.subplots(figsize=(4.5,6)) # adjust image aspect to your data
    # temp data seems to fluctuate more wildly than others, so it is given explicit bounds
    if min and max:
        img = ax.imshow(nc_file[var][0,:,:,0], cmap='jet', origin='lower', vmin=min, vmax=max)
    else:
        img = ax.imshow(nc_file[var][0,:,:,0], cmap='jet', origin='lower')
    cbar = fig.colorbar(img)
    unit = units[variables.index(var)]
    ax.set_title(var + (' (' + unit + ')' if unit != '' else ''))
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    fig.tight_layout(pad=0.4)
    return fig

# save to png file
def save_fig(fig, filename):
    fig.savefig(filename)
    plt.close(fig)

# get the right nc file (out2 vs out3) based on the variable
def get_nc_file(var, num):
    # choose right file depending on variable
    if var in variables2:
        return get_nc_file2(num)
    elif var in variables3:
        return get_nc_file3(num)

def get_nc_file2(num):
    file = '%s/geyser.out2.00%s.nc' %(nc_dir, num)
    return netCDF4.Dataset(file)

def get_nc_file3(num):
    file = '%s/geyser.out3.00%s.nc' %(nc_dir, num)
    return netCDF4.Dataset(file)

# create a movie for a given variable with specified colorbar min/max values
def create_movie(var, output_mp4_file, min=None, max=None):
    filenames = []
    for num in filenums:
        nc_file = get_nc_file(var, num)
        fig = plot_var(nc_file, var, min, max)
        output_file = '%s_%s.png' %(var, num)
        save_fig(fig, output_file)
        filenames.append(output_file)
    
    '''
    # write to gif
    output_gif = './geyser_%s.gif' %var # output gif file
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
    video = cv2.VideoWriter(output_mp4_file, fourcc, 1/frame_duration, (width,height))
    for image in filenames:
        video.write(cv2.imread(image))
    cv2.destroyAllWindows()
    video.release()

    # delete temp png files
    for file in set(filenames):
        if os.path.exists(file):
            os.remove(file)

if __name__ == "__main__":
    main()
