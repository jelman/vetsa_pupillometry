#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 14:57:31 2019

@author: jelman

Script to gather fluency data summarized by Tertiles. Outputs a  a summary 
dataset which averages across trials to give a single value per condition and 
quartile.
"""

import os
import sys
import numpy as np
import pandas as pd
from glob import glob
from datetime import datetime
try:
    # for Python2
    import Tkinter as tkinter
    import tkFileDialog as filedialog
except ImportError:
    # for Python3
    import tkinter
    from tkinter import filedialog

def pivot_wide(dflong):
    # Convert float to integer
    dflong['Seconds'] = dflong['Seconds'].astype(int)
    # Define a mapping dictionary for integer seconds to string
    seconds_mapping = {10: '1_10', 20: '10_20', 30: '20_30'}
    # Replace integer seconds with string using the map function
    dflong['Seconds'] = dflong['Seconds'].map(seconds_mapping)
    # Replace 'Task' column values
    dflong['Task'] = dflong['Task'].replace({'Category' : 'cat', 'Letter' : 'let'})
    # Combine Task and Seconds columns into a single column with '_' delimiter
    dflong['TaskTime'] = dflong.Task + '_' + dflong.Seconds
    dflong = dflong.drop(columns=['Task','Seconds'])
    colnames = ['Dilation', 'Baseline','Diameter', 'BlinkPct', 'ntrials']
    dfwide = dflong.pivot(index="Subject", columns='TaskTime', values=colnames)
    dfwide.columns = ['_'.join([str(col[0]),'fluency',str(col[1])]).strip() for col in dfwide.columns.values]
    condition = ['cat', 'let']
    tertiles = ['1_10','10_20','20_30']
    neworder = [n+'_fluency_'+c+'_'+t for c in condition for t in tertiles for n in colnames]
    dfwide = dfwide.reindex(neworder, axis=1)
    dfwide = dfwide.reset_index()
    dfwide.columns = dfwide.columns.str.lower()
    return dfwide
    
    
    
    
def proc_group(datadir):
    # Gather processed fluency data
    globstr = '*_ProcessedPupil_Tertiles.csv'
    filelist = glob(os.path.join(datadir, globstr))
    # Initiate empty list to hold subject data
    allsubs = []
    for fname in filelist:
        subdf = pd.read_csv(fname)
        unique_subid = subdf.Subject.unique()
        if len(unique_subid) == 1:
            subid = str(subdf['Subject'].iat[0])
        else:
            raise Exception('Found multiple subject IDs in file {0}: {1}'.format(fname, unique_subid))
        subdf['Subject'] = subid
        allsubs.append(subdf)
    
    # Concatenate all subject date
    alldf = pd.concat(allsubs)
    # Save out concatenated data
    date = datetime.today().strftime('%Y-%m-%d')
    # outname_all = ''.join(['fluency_Tertiles_AllTrials_',date,'.csv'])
    # alldf.to_csv(os.path.join(datadir, outname_all), index=False)
    
    # Filter out Tertiles with >50% blinks or entire trials with >50% blinks
    exclude = (alldf.groupby('Subject').BlinkPct.transform(lambda x: x.mean())>.50) | (alldf.BlinkPct>.50)
    alldf = alldf[-exclude]
    # Average across trials within quartile and condition
    pupilcols = ['Subject','Seconds','Dilation','Baseline','Diameter','BlinkPct','Task']
    alldfgrp = alldf[pupilcols].groupby(['Subject','Task','Seconds']).mean().reset_index()
    # Drop Seconds==0.0, this was only just for plotting purposes
    alldfgrp = alldfgrp[alldfgrp.Seconds!=0.0]
    # Get number of trials contributing to each task
    ntrials = alldf.groupby(['Subject','Task','Seconds']).size().reset_index(name='ntrials')
    alldfgrp = alldfgrp.merge(ntrials, on=['Subject','Task','Seconds'], validate="one_to_one")
    # Save out summarized data
    outname_avg = ''.join(['fluency_Tertiles_group_long_',date,'.csv'])
    print('Writing processed group data (long format) to {0}'.format(outname_avg))
    alldfgrp.to_csv(os.path.join(datadir, outname_avg), index=False)
    
    alldfgrp_wide = pivot_wide(alldfgrp)
    outname_wide = ''.join(['fluency_Tertiles_group_wide_',date,'.csv'])
    print('Writing processed group data (wide format) to {0}'.format(outname_wide))
    alldfgrp_wide.to_csv(os.path.join(datadir, outname_wide), index=False)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('USAGE: {} <data directory> '.format(os.path.basename(sys.argv[0])))
        print('Searches for datafiles created by fluency_proc_subject.py for use as input.')
        print('This includes:')
        print('  Fluency_<subject>_ProcessedPupil_Tertiles.csv')
        print('Extracts mean dilation from Tertiles and aggregates over trials.')
        print('')

        root = tkinter.Tk()
        root.withdraw()
        # Select folder containing all data to process
        datadir = filedialog.askdirectory(title='Choose directory containing subject data')
        proc_group(datadir)

    else:
        datadir = sys.argv[1]
        proc_group(datadir)


        
