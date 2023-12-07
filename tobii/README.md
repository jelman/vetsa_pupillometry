# VETSA Pupillometry Processing Pipeline
This repository contains the code for the VETSA pupillometry processing pipeline. The pipeline uses packages listed in the environment.yml file. Data were acquired using Tobii eye trackers and E-prime software starting in wave 4 of VETSA. Pupil were collected during the following tasks:
- Digit span
- Verbal fluency
- Visual short-term memory binding

The code in this repo is based on code written for the [PupAlz](https://github.com/jelman/PupAlz) project. Core processing steps are largely the same, but scripts have been altered to accommodate different data organization and naming conventions. Processing scripts for the VSTMB task are new. 


## Prerequisites
1. Install [Anaconda](https://www.anaconda.com/products/individual)
2. Clone this repository
3. Create a conda environment using the environment.yml file
```
conda env create -f environment.yml
```
4. Activate the environment
```
conda activate vetsa-pupillometry
```

## Preparing data for analysis
- Output from Tobii extensions for E-prime (*.GazeData files) for all subjects should be saved together in task-specific folders on the shared drive ("M drive"). 
- Visual short-term memory binding will also require behavioral variables from the database. 

## Processing steps
1. For each task, run the script `<task name>_proc_subject.py` to process individual subject data. This script will open a file selection window to select all raw subject data files. It will then save processed subject data into the specified output directory. 
2. Run the script `<task name>_proc_group.py` to process group data. This script will open a folder selection window to select the directory containing all processed subject data. It will then save group data into the specified output directory.
