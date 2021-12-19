#!/bin/bash

source config.sh

# first generate the initial mesh:
# ./generate_initial_mesh.sh

####
# mapping files
# ./generate_mapping_files.sh

# domain files
./generate_domain_files.sh


####
# topography
./generate_topo.sh

####
# atm initial condition -- need to make sure topography is done ...
# ./create_atm_initial_condition.sh

####
# dry deposition (atmsrf)
./generate_atmsrf.sh

