#!/bin/bash
echo "#SBATCH --image=docker:opensciencegrid/osgvo-el6:latest"
echo "#SBATCH --volume=\"/global/project/projectdirs/mp107/cvmfs_transfer:/cvmfs\""
echo "#SBATCH -t 06:00:00"
echo "#SBATCH -C knl"
echo "#SBATCH --partition=regular"
