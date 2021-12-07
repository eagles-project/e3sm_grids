#!/bin/bash

# project details
project=m3525

# RRM grid details to specify
dyn_grid_name=enax4v2
atm_grid_name=${dyn_grid_name}pg2
ocn_grid_name=oEC60to30v3
lnd_grid_name=r05

# directory structures to specify
tempest_root=${HOME}/git_repos/tempestremap
squadgen_root=${HOME}/git_repos/SQuadgen
output_root=${CSCRATCH}/e3sm/grids/${atm_grid_name}
inputdata_root=/global/cfs/cdirs/e3sm/inputdata
e3sm_root=${HOME}/git_repos/E3SM
hiccup_root=${HOME}/git_repos/HICCUP
mapping_root=/project/projectdirs/e3sm/mapping
script_dir=${PWD}

# homme_tool
# ...

# input scrip grid files needed for mapping (step 3)
if [ "$lnd_grid_name" == "r0125" ]; then 
    lnd_grid_file=${inputdata_root}/lnd/clm2/mappingdata/grids/MOSART_global_8th.scrip.20180211c.nc   # r0125
fi
if [ "$lnd_grid_name" == "r05" ]; then
    lnd_grid_file=${inputdata_root}/lnd/clm2/mappingdata/grids/SCRIPgrid_0.5x0.5_nomask_c110308.nc    # r05
fi
lnd_scrip_file=${lnd_grid_file}

# ocean grid file
if [ "$ocn_grid_name" == "oRRS18to6v3" ]; then
    ocn_grid_file=${inputdata_root}/ocn/mpas-o/oRRS18to6v3/ocean.oRRS18to6v3.scrip.181106.nc
fi
if [ "$ocn_grid_name" == "oEC60to30v3" ]; then
    ocn_grid_file=${inputdata_root}/ocn/mpas-o/oEC60to30v3/ocean.oEC60to30v3.scrip.181106.nc
fi
ocn_scrip_file=${ocn_grid_file}

# create directories if necessary
mkdir -p $output_root

# Machine and compiler will be used in some of the scripts to get proper environment
machine="cori-knl"
fortran_compiler="ifort"
compiler="intel"

# Need an environment with at least nco and ncl; can create this with conda like:
# > conda create --name ncl -c conda-forge nco ncl

# use e3sm_unified by default
source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_cori-knl.sh
