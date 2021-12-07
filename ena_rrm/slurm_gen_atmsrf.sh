#!/bin/bash
#SBATCH -N 1
#SBATCH --time=00:30:00
#SBATCH --job-name=gen_atmsrf
#SBATCH --qos=debug
#SBATCH -C knl

source config.sh
source .env_mach_specific.sh

# Set full name for physics grid
physics_grid=${atm_grid_name}

cd ${e3sm_root}/components/eam/tools/mkatmsrffile || exit 1

# Run the tool from compute node
mkatmsrffile=${e3sm_root}/components/eam/tools/mkatmsrffile/mkatmsrffile
${mkatmsrffile}
