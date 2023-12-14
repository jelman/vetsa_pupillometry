# VETSA Pupillometry Processing Pipeline (Tobii)
This repository contains the code for the VETSA pupillometry processing pipeline. The pipeline uses packages listed in the environment.yml file. Data were acquired using Tobii eye trackers and E-prime software starting in wave 4 of VETSA. Pupil were collected during the following tasks:
- Digit span
- Verbal fluency
- Visual short-term memory binding

The code in this repo is based on code written for the [PupAlz](https://github.com/jelman/PupAlz) project. Core processing steps are largely the same, but scripts have been altered to accommodate different data organization and naming conventions. Processing scripts for the VSTMB task are new. 

There are several changes to Digit Span and Fluency task acquisition and processing:
- The Digit Span task includes 2 baseline tasks in which 9 digits are read aloud. Participants are instructucted only to listen to the digits but not try to remember them (with a note that they will be asked to remember digits on other trials). Pupil diameter during active memory trials can be compared to dilation during the baseline trials at the corresponding digit to isolate auditory processing from memory encoding.
- The Fluency task includes a 2 second baseline period at the beginning of each trial prior to instructions and letter/category presentation. This provides a baseline free from the auditory stimuli or initial stages of word retrieval processes. 
- The fluency task was 30 seconds in duration rather than 60 seconds. Group level data are summarized in tertiles (10s) rather than quartiles (15s).


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

## Preparing data for analysis
- Output from Tobii extensions for E-prime (*.GazeData files) for all subjects should be saved together in task-specific folders on the shared drive ("M drive"). 
- Visual short-term memory binding will also require behavioral variables from the database. 

## Processing steps
1. For each task, run the script `<task name>_proc_subject.py` to process individual subject data. This script will open a file selection window to select all raw subject data files. It will then save processed subject data into the specified output directory. 
2. Run the script `<task name>_proc_group.py` to process group data. This script will open a folder selection window to select the directory containing all processed subject data. It will then save group data into the specified output directory.
