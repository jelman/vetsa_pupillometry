# VETSA Pupillometry Processing Pipeline

Script to parse and process pupillometry data from VETSA study.

This repo contains two sets of scripts, one for processing data from NeurOptics pupillometry device and one for processing data from Tobii eye tracker. The NeurOptics devices were used in VETSA waves 2 and 3. The Tobii devices were used in VETSA wave 4 and based on code written for the PupAlz study ([PupAlz repo](https://github.com/jelman/PupAlz)). 

See the README files in the NeurOptics and Tobii directories for more information about processing data from each device.

## Prerequisites
1. Install [Anaconda](https://www.anaconda.com/products/individual)
2. Clone this repository
```
git clone https://github.com/jelman/vetsa_pupillometry.git
```
3. Create a conda environment using the environment.yml file
```
conda env create -f environment.yml
```
4. Activate the environment
```
conda activate vetsa-pupillometry
```
