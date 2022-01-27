#!/usr/bin/env python
# ==================================================================================================
# HICCUP - Hindcast Initial Condition Creation Utility/Processor
# This tool automates the creation of atmospheric initial condition files for 
# E3SM using user supplied file for atmospheric and sea surface conditions.
# ==================================================================================================
import os, optparse
from hiccup import hiccup_data_class as hdc
from hiccup import hiccup_state_adjustment as hsa
# ------------------------------------------------------------------------------
# Parse the command line options
parser = optparse.OptionParser()
parser.add_option('--hgrid',    dest='horz_grid',default=None,help='Sets the output horizontal grid')
parser.add_option('--vgrid',    dest='vert_grid',default=None,help='Sets the output vertical grid')
parser.add_option('--init_date',dest='init_date',default=None,help='Sets the initialization date YYYY-MM-DD')
parser.add_option('--vgrid_dir', dest='vgrid_dir', default=os.getenv('HOME')+'/E3SM/vert_grid_files',
                  help='Directory containing vertical grid files')
parser.add_option('--vgrid_file', dest='vert_file_name', default=None,
                  help='Specified vertical grid file')
parser.add_option('--topo_file', dest='topo_file_name', default=None,
                  help='Specified topography file')
parser.add_option('--hgrid_file', dest='horz_file_name',
                  default='/global/cscratch1/sd/crjones/e3sm/grids/enax4v3pg2/enax4v3.g',
                  help='Specify horizontal grid file')
parser.add_option('--output_dir', dest='output_dir', default=None,
                  help='Destination for output files, defaults to $SCRATCH/HICCUP/data')
(opts, args) = parser.parse_args()
# ------------------------------------------------------------------------------
# Logical flags for controlling what this script will do
# Comment out a line or set to False to disable a section
verbose = True            # Global verbosity flag
# unpack_nc_files = True    # unpack data files (convert short to float)
create_map_file = True    # grid and map file creation
remap_data_horz = True    # horz remap, variable renaming
do_sfc_adjust   = True    # perform surface T and P adjustments
remap_data_vert = True    # vertical remap
do_state_adjust = True    # post vertical interpolation adjustments
combine_files   = True    # combine temporary data files and delete
# create_sst_data = True    # sst/sea ice file creation
# ------------------------------------------------------------------------------

# opts.vert_grid = 'L50'
# opts.init_date = '2008-10-01'

# Specify output atmosphere horizontal grid
if opts.horz_grid is not None:
    dst_horz_grid = opts.horz_grid 
else:
    dst_horz_grid = 'enax4v2pg2'

# Specify output atmosphere vertical grid
if opts.vert_grid is not None:
    dst_vert_grid, vert_file_name = opts.vert_grid, opts.vert_file_name
    if vert_file_name is None:
        if dst_vert_grid=='L72':
            vert_file_name = f'{opts.vgrid_dir}/L72_E3SM.nc'
        elif dst_vert_grid == 'L50':
            vert_file_name = f'{opts.vgrid_dir}/L50_v2.nc'
        elif dst_vert_grid == 'L100':
            vert_file_name = f'{opts.vgrid_dir}/L100_v1.nc'
        elif dst_vert_grid == 'L120':
            vert_file_name = f'{opts.vgrid_dir}/L120_v1.nc'
        else:
            raise InputError(f'No vertical grid specified for {dst_vert_grid}')
else:
    raise InputError('No vertical grid provided!')

# specify date of data
if opts.init_date is not None:
    init_date = opts.init_date
else:
    raise InputError('No init_date provided!')
    # init_date = '2008-10-01'
init_year = int(init_date.split('-')[0])

# Specify output file names
data_root = os.getenv('SCRATCH')+'/HICCUP/data/' # NERSC
output_root = data_root if opts.output_dir is None else opts.output_dir
output_atm_file_name = f'{output_root}/HICCUP.atm_era5.{init_date}.{dst_horz_grid}.{dst_vert_grid}.nc'
output_sst_file_name = f'{output_root}/HICCUP.sst_noaa.{init_date}.nc'

# set topo file - replace this with file path if no defalt is set
if opts.topo_file_name is not None:
    topo_file_name = opts.topo_file_name
else:
    topo_file_name = '/global/cscratch1/sd/crjones/e3sm/grids/enax4v0pg2/USGS-gtopo30_enax4v0pg2_12xdel2.nc'

# Create data class instance, which includes xarray file dataset objects
# and variable name dictionaries for mapping between naming conventions.
# This also checks input files for required variables
hiccup_data = hdc.create_hiccup_data(name='ERA5'
                                    ,atm_file=f'{data_root}ERA5.atm.{init_date}.nc'
                                    ,sfc_file=f'{data_root}ERA5.sfc.{init_date}.nc'
                                    ,sstice_name='NOAA'
                                    ,sst_file=f'{data_root}sst.day.mean.{init_year}.nc'
                                    ,ice_file=f'{data_root}icec.day.mean.{init_year}.nc'
                                    ,topo_file=topo_file_name
                                    ,dst_horz_grid=dst_horz_grid
                                    ,dst_vert_grid=dst_vert_grid
                                    ,output_dir=output_root
                                    ,grid_dir=data_root
                                    ,map_dir=data_root
                                    ,tmp_dir=data_root
                                    ,verbose=verbose
                                    ,check_input_files=True)

# overwrite grid data
hiccup_data.dst_horz_grid = dst_horz_grid
hiccup_data.dst_grid_file = opts.horz_file_name

# Print some informative stuff
print('\n  Input Files')
print(f'    input atm files: {hiccup_data.atm_file}')
print(f'    input sfc files: {hiccup_data.sfc_file}')
print(f'    input sst files: {hiccup_data.sst_file}')
print(f'    input ice files: {hiccup_data.ice_file}')
print(f'    input topo file: {hiccup_data.topo_file}')
print('\n  Output files')
print(f'    output atm file: {output_atm_file_name}')
print(f'    output sst file: {output_sst_file_name}')

# Get dict of temporary files for each variable
file_dict = hiccup_data.get_multifile_dict()

# ------------------------------------------------------------------------------
# Make sure files are "unpacked" (may take awhile, so only do it if you need to)
# ------------------------------------------------------------------------------
if 'unpack_nc_files' not in locals(): unpack_nc_files = False
if unpack_nc_files:

    hiccup_data.unpack_data_files()

# ------------------------------------------------------------------------------
# Create grid and mapping files
# ------------------------------------------------------------------------------
if 'create_map_file' not in locals(): create_map_file = False
if create_map_file :

    # Create grid description files needed for the mapping file
    hiccup_data.create_src_grid_file()
    if hiccup_data.dst_grid_file is None: hiccup_data.create_dst_grid_file()
    # hiccup_data.create_dst_grid_file()
    # hiccup_data.dst_grid_file = '/global/homes/w/whannah/E3SM/data_grid/conusx4v1.g'

    # Create mapping file
    hiccup_data.create_map_file(src_type='FV', dst_type='GLL')

# ------------------------------------------------------------------------------
# perform multi-file horizontal remap
# ------------------------------------------------------------------------------
if 'remap_data_horz' not in locals(): remap_data_horz = False
if remap_data_horz :

    # Horizontally regrid the data
    hiccup_data.remap_horizontal_multifile(file_dict)

    # Rename variables to match what the model expects
    hiccup_data.rename_vars_multifile(file_dict=file_dict)

    # Add time/date information
    hiccup_data.add_time_date_variables_multifile(file_dict=file_dict)

# ------------------------------------------------------------------------------
# Do surface adjustments
# ------------------------------------------------------------------------------
if 'do_sfc_adjust' not in locals(): do_sfc_adjust = False
if do_sfc_adjust:

    hiccup_data.surface_adjustment_multifile(file_dict=file_dict)

# ------------------------------------------------------------------------------
# Vertically remap the data
# ------------------------------------------------------------------------------
if 'remap_data_vert' not in locals(): remap_data_vert = False
if remap_data_vert :

    hiccup_data.remap_vertical_multifile(file_dict=file_dict
                                        ,vert_file_name=vert_file_name)

# ------------------------------------------------------------------------------
# Perform final state adjustments on interpolated data and add additional data
# ------------------------------------------------------------------------------
if 'do_state_adjust' not in locals(): do_state_adjust = False
if do_state_adjust :

    hiccup_data.atmos_state_adjustment_multifile(file_dict=file_dict)

# ------------------------------------------------------------------------------
# Combine files
# ------------------------------------------------------------------------------
if 'combine_files' not in locals(): combine_files = False
if combine_files :

    # Combine and delete temporary files
    hiccup_data.combine_files(file_dict=file_dict
                             ,delete_files=True
                             ,output_file_name=output_atm_file_name)

    # Clean up the global attributes of the file
    hiccup_data.clean_global_attributes(file_name=output_atm_file_name)

# ------------------------------------------------------------------------------
# Create SST/sea ice file
# ------------------------------------------------------------------------------
if 'create_sst_data' not in locals(): create_sst_data = False
if create_sst_data :

    # create grid and mapping files
    overwrite = False
    hiccup_data.sstice_create_src_grid_file(force_overwrite=overwrite)
    hiccup_data.sstice_create_dst_grid_file(force_overwrite=overwrite)
    hiccup_data.sstice_create_map_file(force_overwrite=overwrite)

    # Remap the sst/ice data after time slicing and combining (if necessary)
    hiccup_data.sstice_slice_and_remap(output_file_name=output_sst_file_name,
                                       time_slice_method='match_atmos',
                                       atm_file=output_atm_file_name)

    # Rename the variables and remove unnecessary variables and attributes
    hiccup_data.sstice_rename_vars(output_file_name=output_sst_file_name)

    # Adjust final SST/ice data to fill in missing values and limit ice fraction
    hiccup_data.sstice_adjustments(output_file_name=output_sst_file_name)

# ------------------------------------------------------------------------------
# Print final output file name
# ------------------------------------------------------------------------------

print()
print(f'output_atm_file_name: {output_atm_file_name}')
print(f'output_sst_file_name: {output_sst_file_name}')
print()

# Print summary of timer info
hdc.print_timer_summary()

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
