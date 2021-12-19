#!/bin/bash
source config.sh   # config file

# Step 0: Must specify refinement patch with png of mask (refine_file defined in config.sh)
# Step 1: Use SQuadgen to generate the atm dynamics grid
dyn_grid_file=${output_root}/${dyn_grid_name}.g
$squadgen_root/SQuadGen --refine_level $refine_level --resolution 32 --refine_file $refine_file \
			--invert --smooth_type SPRING --smooth_iter 20 --smooth_dist 3 \
			--output $dyn_grid_file

# Step 2A: Generate pg2 atm_grid_name:
atm_grid_file=${output_root}/${atm_grid_name}.g
$tempest_root/bin/GenerateVolumetricMesh --in $dyn_grid_file --out $atm_grid_file --np 2 --uniform

# Generate SCRIP file
$tempest_root/bin/ConvertExodusToSCRIP --in $atm_grid_file --out ${output_root}/${atm_grid_name}_scrip.nc

# Note to self: add notebook or script to validate this step completed correctly and the grid looks good
