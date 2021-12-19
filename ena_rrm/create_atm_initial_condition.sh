#!/bin/bash

# create atm initial condition using HICCUP [WIP]
# See: https://github.com/E3SM-Project/HICCUP

# this script will need to be cleaned up
source config.sh

# load conda environment with dependencies for HICCUP
# (note: can't use e3sm-unified because lack permission to hiccup module to search path)
#
# hiccup_env: (note)
# > conda create --name hiccup_env -c conda-forge xarray dask pandas scipy netcdf4 hdf5 cdsapi tempest-remap nco
conda activate hiccup_env

# hiccup initial condition for specific date (assuming initial hindcast data was already grabbed)
# TODO: update this script with example using get_hindcast_data.ERA5.py
#       to grab ICs for a new date

vgrid=L72
init_date=2017-07-18    # yyyy-mm-dd format
vgrid_dir=${hiccup_root}/files_vert
vgrid_file=${vgrid_dir}/vert_coord_E3SM_L72.nc

topo_file=${output_root}/USGS-gtopo30_${atm_grid_name}_12xdel2.nc
hgrid_file=${output_root}/${dyn_grid_name}.g

python create_initial_condition_from_obs_ena.py --vgrid $vgrid --init_date $init_date \
       --hgrid $atm_grid_name \
       --vgrid_dir $vgrid_dir --vgrid_file $vgrid_file --topo_file $topo_file --hgrid_file $hgrid_file
