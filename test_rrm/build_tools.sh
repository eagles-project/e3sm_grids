#!/bin/bash

source config.sh

#########################################
# Build tools needed for RRM generation
#########################################

###########################
# gen_domain tool
###########################
module unload cray-netcdf-hdf5parallel
module unload cray-hdf5-parallel
module load cray-netcdf

export NETCDF_ROOT=$NETCDF_DIR
export FC=ftn

gen_domain=${e3sm_root}/cime/tools/mapping/gen_domain_files/gen_domain

# Configure and build
cd `dirname ${gen_domain}`/src
../../../configure --macros-format Makefile --mpilib mpi-serial
# gmake clean
gmake

#########################
# mkatmsrffile
#########################
# Note: for running on login node: use cray-netcdf module, do not source .env_mach_specific.sh
cd ${e3sm_root}/components/eam/tools/mkatmsrffile || exit 1
../../../../cime/tools/configure --macros-format=Makefile || exit 1
source .env_mach_specific.sh || exit 1
export NETCDF_ROOT=$NETCDF_DIR
export FC=ftn

# make clean
make

############################################
# homme_tool
#   Note: homme_build defined in config.sh
#         default location: $SCRATCH/homme
############################################
machine=cori-knl
compiler=ifort

homme_root=${e3sm_root}/components/homme
homme_exe=${homme_build}/src/tool/homme_tool
if [ ! -e ${homme_exe} ]; then
    mkdir -p ${homme_build} && cd ${homme_build}
    
    # load necessary modules
    eval `$e3sm_root/cime/scripts/Tools/get_case_env`

    export NETCDF_ROOT=$NETCDF_DIR
    export FC=ftn
    
    # compile homme
    cmake -C ${homme_root}/cmake/machineFiles/${machine}.cmake ${homme_root}
    make -j4 homme_tool
    if [ $? -ne 0 ]; then
        echo "homme_tool build failed."
        exit 1
    fi
fi

##########################
# cube_to_target
##########################

# load appropriate modules
cd ${e3sm_root}/components/eam/tools/topo_tool/cube_to_target
${e3sm_root}/cime/tools/configure 
source .env_mach_specific.sh

# set environment variables for Makefile
export FC=ifort
export LIB_NETCDF=${NETCDF_DIR}/lib
export INC_NETCDF=${NETCDF_DIR}/include

# build
# make clean
make
