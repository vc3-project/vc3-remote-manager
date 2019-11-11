#! /bin/bash

#echo "#SBATCH --image=docker:opensciencegrid/osgvo-el7:latest"
#echo "#SBATCH --module=cvmfs"
echo "#SBATCH -t 02:00:00"
# echo "#SBATCH --partition=shared"
# echo "#SBATCH --partition=regularx"
echo "#SBATCH -C haswell"
echo "#SBATCH --partition=regular"
echo "#SBATCH -L SCRATCH"
