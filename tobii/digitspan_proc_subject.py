# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 12:00:45 2016

@author: jelman

This script takes Tobii .gazedata file from digit span as input. It 
first performs interpolation and filtering, Dilation at each second is calculated
for each load after baselining. Baseline is the average dilation during the 
"Ready" phase.

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
    palette = sns.cubehelix_palette(len(pupildf.Load.unique()))
    p = sns.lineplot(data=pupildf, x="Seconds",y="Dilation", hue="Load", palette=palette, legend="brief", errorbar=None)
    plt.ylim(-.2, .5)
    plt.tight_layout()
    plot_outname = pupil_fname.replace("_ProcessedPupil.csv", "_PupilPlot.png")
    p.figure.savefig(plot_outname)
    plt.close()
    
    
def clean_trials(trialevents):
    resampled_dict = {}
    for trial in trialevents.Trial.unique():
        starttime, stoptime =  trialevents.loc[trialevents.Trial==trial,'RTTime'].iloc[[0,-1]]
        rawtrial = trialevents.loc[(trialevents.RTTime>=starttime) & (trialevents.RTTime<=stoptime)]
        cleantrial = pupil_utils.deblink(rawtrial)
        string_cols = ['Load', 'Trial', 'TrialId', 'Condition']
        trial_resamp = pupil_utils.resamp_filt_data(cleantrial, filt_type='low', string_cols=string_cols)
        baseline = trial_resamp.loc[trial_resamp.Condition=='Ready', 'PupilDiameterLRFilt'].last('250ms').mean()
        baseline_blinks = trial_resamp.loc[trial_resamp.Condition=='Ready', 'BlinksLR'].last('250ms').mean()
        if baseline_blinks > .5:
            baseline = np.nan
        trial_resamp['Baseline'] = baseline
        trial_resamp['Dilation'] = trial_resamp['PupilDiameterLRFilt'] - trial_resamp['Baseline']
        trial_resamp = trial_resamp[trial_resamp.Condition=='Record']
        trial_resamp.index = pd.DatetimeIndex((trial_resamp.index - trial_resamp.index[0]).astype(np.int64))
        resampled_dict[trial] = trial_resamp        
    dfresamp = pd.concat(resampled_dict, names=['Trial','Timestamp'])
    return dfresamp
    
def define_condition(trialdf):
    trialdf['Condition'] = np.where((trialdf.RTTime - trialdf.RTTime.iloc[0]) / 1000. > 1., 'Record', 'Ready')
    return trialdf


def get_trial_events(df):
    """
    Create dataframe of trial events. This includes:
        Load: [Baseline, 3, 6, 9] Number of digits to recall
        Trial: Lists load and trial number within each load
        Condition: ['Ready', 'Record'] Phase of trial
    First finds timestamps where each load trial begins and ends. Appends info
    about the load and trial number. Also defines phase of each trial. 
    """
    trials = [x for x in df.Trial.unique()]
    # Find last index of each load
    lastidx = [df[df.Trial==x].index[-1] for x in trials]
    stopidx = [x + 1 for x in lastidx]
    startidx = stopidx[:-1]
    startidx.insert(0,0)
    triallist = []
    for i, cond in enumerate(trials):
        loaddf = df[startidx[i]:stopidx[i]]
        loaddf = loaddf[loaddf['CurrentObject']=='Ready']
        # Confirm TrialId is A, B, or C
        assert all(x in ['A','B','C'] for x in loaddf['TrialId'].unique())        
        loaddf = loaddf.groupby('Trial').apply(define_condition)
        triallist.append(loaddf)
    trialevents = pd.concat(triallist)    
    return trialevents


def recode_digitlist(digitlist):
    """Recode DigitList values to """
    digitlist = digitlist.str.replace('ListLoad','')
    digitlist = digitlist.str.replace('1','A')
    digitlist = digitlist.str.replace('2','B')
    return digitlist
   
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
        df['Subject'] = subid
        # Load column is incorrect, remove. It will be generated correctly from DigitList
        df = df.drop('Load', axis=1)
        # Recode DigitList values
        df['Trial'] = recode_digitlist(df['DigitList'])
        # Convert PupilDiameterLeftEye and PupilDiameterRightEye to numeric
        df['PupilDiameterLeftEye'] = pd.to_numeric(df['PupilDiameterLeftEye'], errors='coerce')
        df['PupilDiameterRightEye'] = pd.to_numeric(df['PupilDiameterRightEye'], errors='coerce')      
        # Create Load and TrialId columns
        df['Load'] = df['Trial'].str[:-1]
        df['TrialId'] = df['Trial'].str[-1]
        trialevents = get_trial_events(df)
        dfresamp = clean_trials(trialevents)
        dfresamp = dfresamp.reset_index(level='Timestamp').set_index(['Load','Trial'])
        # # Save out dfresamp for cleaned pupil at 30Hz for individuals trials 
        # pupil_outname = pupil_utils.get_proc_outfile(fname, '_ProcessedPupil30Hz.csv')
        # pupildf.to_csv(pupil_outname, index=True)
        
        dfresamp1s = dfresamp.groupby(level=['Load','Trial']).apply(lambda x: x.resample('1s', on='Timestamp', closed='right', label='right').mean(numeric_only=True)).reset_index()
        dfresamp1s['Subject'] = subid
        # Select and rename columns of interest
        pupilcols = ['Subject', 'Trial', 'Load', 'Timestamp', 'Dilation',
                     'Baseline', 'PupilDiameterLRFilt', 'BlinksLR']
        dfresamp1s = dfresamp1s[pupilcols].rename(columns={'PupilDiameterLRFilt':'Diameter',
                                                 'BlinksLR':'BlinkPct'})
        # Set samples with >50% blinks to missing    
        dfresamp1s.loc[dfresamp1s.BlinkPct>.5, ['Dilation','Baseline','Diameter','BlinkPct']] = np.nan
        # Drop missing samples and average of trials within load
        pupildf = dfresamp1s.groupby(['Load','Timestamp']).mean(numeric_only=True)
        # Add number of non-missing trials that contributed to each sample average
        pupildf['ntrials'] = dfresamp1s.dropna(subset=['Dilation']).groupby(['Load','Timestamp']).size()
        # Set subject ID and session as (as type string)
        pupildf['Subject'] = subid
        # Add column with seconds and format Timestamp
        pupildf = pupildf.reset_index()
        pupildf['Timestamp'] = pupil_utils.convert_timestamp(pupildf.Timestamp)
        pupildf['Seconds'] = pupildf['Timestamp'].apply(pupil_utils.format_timedelta_seconds)
        pupildf['Timestamp'] = pupildf['Timestamp'].apply(pupil_utils.format_timedelta_hms)
        # Generate output filename
        pupil_outname = os.path.join(outdir, 'DigitSpan_' + subid + '_ProcessedPupil.csv')
        print('Writing processed data to {0}'.format(pupil_outname))
        # Save out data and plots
        pupildf.to_csv(pupil_outname, index=False)
        plot_trials(pupildf, pupil_outname)


    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('')
        print('USAGE: {} <raw pupil file> <output dir>'.format(os.path.basename(sys.argv[0])))
        print("""Processes single subject data from digit span task and outputs
              csv files for use in further group analysis. Takes eye tracker 
              data text file (*.gazedata) as input. Removes artifacts, filters, 
              and calculates dilation per 1sec.""")
        root = tkinter.Tk()
        root.withdraw()
        # Select files to process
        filelist = filedialog.askopenfilenames(parent=root,
                                              title='Choose Digit Span pupil gazedata file to process')
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

