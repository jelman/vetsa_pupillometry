# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 12:00:45 2016

@author: jelman

This script takes Tobii .gazedata file from auditory oddball as input. It 
first performs interpolation and filtering, Then peristimulus timecourses 
are created for target and standard trials after baselining. Trial-level data 
and average PSTC waveforms data are output for further group processing using 
(i.e., with oddball_proc_group.py). 

Some procedures and parameters adapted from:
Jackson, I. and Sirois, S. (2009), Infant cognition: going full factorial 
    with pupil dilation. Developmental Science, 12: 670-679. 
    doi:10.1111/j.1467-7687.2008.00805.x

Hoeks, B. & Levelt, W.J.M. Behavior Research Methods, Instruments, & 
    Computers (1993) 25: 16. https://doi.org/10.3758/BF03204445
"""

from __future__ import division, print_function, absolute_import
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pupil_utils
try:
    # for Python2
    import Tkinter as tkinter
    import tkFileDialog as filedialog
except ImportError:
    # for Python3
    import tkinter
    from tkinter import filedialog


def plot_trials(pupildf, pupil_fname):
    sns.set_style("ticks")
    # Define a custom color palette
    condition_colors = {'C': 'blue', 'L': 'dodgerblue', 'GirlsNames': 'red',  'Vegetables': 'lightcoral'}
    palette = [condition_colors[condition] for condition in pupildf.Condition.unique()]
    p = sns.lineplot(data=pupildf, x="Seconds", y="Dilation", hue="Condition", palette=palette, legend="brief")
    plt.ylim(-1.0, 1.0)
    plt.tight_layout()
    # Set the ordering of the legend
    handles, labels = p.get_legend_handles_labels()
    ordered_labels = ['C', 'L', 'GirlsNames', 'Vegetables']
    ordered_handles = [handles[labels.index(label)] for label in ordered_labels]
    p.legend(ordered_handles, ordered_labels, loc='best')
    # Add shading for baseline period
    p.axvspan(-6, -4, alpha=0.2, color='lightgreen', zorder=0)
    # Add shading for instruction period
    p.axvspan(-4, 0, alpha=0.4, color='lightgray', zorder=0)
    plot_outname = pupil_fname.replace("_ProcessedPupil.csv", "_PupilPlot.png")
    p.figure.savefig(plot_outname)
    plt.close()
    
    
def clean_trials(df):
    resampled_dict = {}
    conditions = df.Condition.unique()
    # If there are not 4 trials, raise an error
    if len(conditions) != 4:
        raise Exception('Expected 4 trials, subject has {} trials'.format(len(conditions)))
    # If there are 4 trials, check that they are ['C','L','Vegetables','GirlsNames']
    elif set(conditions) != set(['C','L','GirlsNames','Vegetables']):
        raise Exception('Expected trials to be ["C","L","GirlsNames","Vegetables"], subject has {}'.format(conditions))
    # Clean each trial
    for condition in conditions:
        rawtrial = df.loc[df.Condition==condition]
        # Fill missing CurrentObject values. Use forward then backward fill
        rawtrial['CurrentObject'] = rawtrial['CurrentObject'].fillna(method='ffill').fillna(method='bfill')
        rawtrial = rawtrial.loc[rawtrial.CurrentObject != "Fixation"]
        cleantrial = pupil_utils.deblink(rawtrial)
        trial_resamp = pupil_utils.resamp_filt_data(cleantrial, filt_type='low', string_cols=['CurrentObject', 'Condition'])
        trial_resamp = trial_resamp.reset_index()
        # Calculate baseline when CurrentObject is 'Baseline'
        baseline = trial_resamp.loc[trial_resamp.CurrentObject=='Baseline', 'PupilDiameterLRFilt'].mean(numeric_only=True)
        trial_resamp['Baseline'] = baseline
        trial_resamp['Dilation'] = trial_resamp['PupilDiameterLRFilt'] - trial_resamp['Baseline']
        # Set Timestamp to 0 when CurrentObject is "RecordLetter"
        trial_resamp['Timestamp'] = trial_resamp['RTTime'] - trial_resamp.loc[trial_resamp.CurrentObject=='RecordLetter', 'RTTime'].iloc[0]
        trial_resamp['Timestamp'] = pd.to_datetime(trial_resamp.Timestamp.values.astype(np.int64), unit='ms')        
        resampled_dict[condition] = trial_resamp
    dfresamp = pd.concat(resampled_dict, names=['Condition','Timestamp'])
    return dfresamp
    

   
def proc_subject(filelist, outdir):
    """Given an infile of raw pupil data, saves out:
        1. Session level data with dilation data summarized for each trial
        2. Dataframe of average peristumulus timecourse for each condition
        3. Plot of average peristumulus timecourse for each condition
        4. Percent of samples with blinks """
    for fname in filelist:
        print('Processing {}'.format(fname))
        if fname.lower().endswith(".gazedata") | fname.lower().endswith(".csv") | fname.lower().endswith(".txt"):
            df = pd.read_csv(fname, sep="\t")
        elif fname.lower().endswith(".xlsx"):
            df = pd.read_excel(fname)
        else: 
            raise IOError('Could not open {}'.format(fname))  
        subid = pupil_utils.get_vetsaid(df, fname)
        # Convert PupilDiameterLeftEye and PupilDiameterRightEye to numeric
        df['PupilDiameterLeftEye'] = pd.to_numeric(df['PupilDiameterLeftEye'], errors='coerce')
        df['PupilDiameterRightEye'] = pd.to_numeric(df['PupilDiameterRightEye'], errors='coerce')      
        # Assign conditions to task. Letter: ['C', 'L']; Category: ['Vegetables', 'GirlsNames']
        dfresamp = clean_trials(df)
        ### Create data resampled to 1 second
        dfresamp1s = dfresamp.groupby(level='Condition').apply(lambda x: x.resample('1s', on='Timestamp', closed='right', label='right').mean(numeric_only=True))
        pupilcols = ['Subject', 'Condition', 'Timestamp', 'Dilation', 'Baseline',
                     'PupilDiameterLRFilt', 'BlinksLR']
        pupildf = dfresamp1s.reset_index()[pupilcols].sort_values(by=['Condition','Timestamp'])
        pupildf = pupildf[pupilcols].rename(columns={'PupilDiameterLRFilt':'Diameter',
                                         'BlinksLR':'BlinkPct'})
        # Set subject ID and session as (as type string)
        pupildf['Subject'] = subid
        # Add column with seconds and format Timestamp
        pupildf['Timestamp'] = pupil_utils.convert_timestamp(pupildf.Timestamp)
        pupildf['Seconds'] = pupildf['Timestamp'].apply(pupil_utils.format_timedelta_seconds)
        pupildf['Timestamp'] = pupildf['Timestamp'].apply(pupil_utils.format_timedelta_hms)
        pupildf['Task'] = pupildf['Condition'].apply(lambda x: 'Letter' if x in ['C', 'L'] else ('Category' if x in ['Vegetables', 'GirlsNames'] else np.nan)) 
        # Only keep samples up to 30.0 seconds
        pupildf = pupildf[pupildf.Seconds <= 30.0]
        # Generate output filename
        pupil_outname = os.path.join(outdir, 'Fluency_' + subid + '_ProcessedPupil.csv')
        print('Writing processed data to {0}'.format(pupil_outname))
        pupildf.to_csv(pupil_outname, index=False)
        plot_trials(pupildf, pupil_outname)
        
        #### Create data for 15 second blocks
        dfresamp10s = dfresamp.groupby(level=['Condition']).apply(lambda x: x.resample('10s', on='Timestamp', closed='right', label='right').mean(numeric_only=True))
        pupilcols = ['Subject', 'Condition', 'Timestamp', 'Dilation', 'Baseline',
                     'PupilDiameterLRFilt', 'BlinksLR']        
        pupildf10s = dfresamp10s.reset_index()[pupilcols]
        pupildf10s = pupildf10s[pupilcols].rename(columns={'PupilDiameterLRFilt':'Diameter',
                                         'BlinksLR':'BlinkPct'})
        # Set subject ID as (as type string)
        pupildf10s['Subject'] = subid
        pupildf10s['Timestamp'] = pupil_utils.convert_timestamp(pupildf10s.Timestamp)
        pupildf10s['Seconds'] = pupildf10s['Timestamp'].apply(pupil_utils.format_timedelta_seconds)
        pupildf10s['Timestamp'] = pupildf10s['Timestamp'].apply(pupil_utils.format_timedelta_hms)
        pupildf10s['Task'] = pupildf10s['Condition'].apply(lambda x: 'Letter' if x in ['C', 'L'] else ('Category' if x in ['Vegetables', 'GirlsNames'] else np.nan)) 
        # Remove samples after 30.0 seconds
        pupildf10s = pupildf10s[pupildf10s.Seconds <= 30.0]
        pupil10s_outname = os.path.join(outdir, 'Fluency_' + subid + '_ProcessedPupil_Tertiles.csv')
        'Writing quartile data to {0}'.format(pupil10s_outname)
        pupildf10s.to_csv(pupil10s_outname, index=False)



    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('')
        print('USAGE: {} <raw pupil file> <output dir>'.format(os.path.basename(sys.argv[0])))
        print("""Processes single subject data from fluency task and outputs csv
              files for use in further group analysis. Takes eye tracker data 
              text file (*.gazedata) as input. Removes artifacts, filters, and 
              calculates dilation per 1s.Also creates averages over 10s blocks.""")
        print('')
        root = tkinter.Tk()
        root.withdraw()
        # Select files to process
        filelist = filedialog.askopenfilenames(parent=root,
                                              title='Choose Fluency pupil gazedata file to process')       
        filelist = list(filelist)
        # Select folder to save processed data
        outdir = filedialog.askdirectory(parent=root,
                                         title='Choose folder to save processed data')
        # Run script
        proc_subject(filelist, outdir)

    else:
        filelist = [os.path.abspath(f) for f in sys.argv[1:]]
        outdir = sys.argv[2]
        proc_subject(filelist, outdir)

