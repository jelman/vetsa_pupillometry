#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 13:43:18 2018

@author: jelman

This script checks data from pupillometers against database of entered day of 
testing information for unmatched timestamps. These can be used to identify 
missing entries or miscoded times. 

Requires an input directory of pupil data that has been parsed by the script 
parsePupilData.py, as well as behavioral data from the VETSA database. Output 
will show full list of joined timestamps, both matched and unmatched. 

"""

import os, sys
import pandas as pd
import numpy as np
import argparse
import string
from datetime import datetime
import itertools
import Tkinter,tkFileDialog
from glob import glob


def rotate(strg,n):
    """ Create function to rotate characters in a string from front to back"""
    return strg[n:] + strg[:n]


def get_pupil_files(indir, pttrn='*_Pupil_*Parsed_*.csv'):
    """Search for pupil files based on filename in given directory"""
    globstr = os.path.join(indir, pttrn)
    filelist = glob(globstr)
    return filelist


def merge_parsed_files(infiles):
    """Loop through pupil files, load, and append to dataframe"""
    pupildf_list = []
    for infile in infiles:
        # Load parsed pupil data
        subjdf = pd.read_csv(infile, sep=",")
        # Append to list
        pupildf_list.append(subjdf)
    # Merge individual files
    pupildf = pd.concat(pupildf_list)
    return pupildf


def get_pupil_times(pupildf):
    """Get timestamp and data columns from pupillometer file"""
    pupilcols = ['Subject ID', 'Date', 'Time', 'Measurement Duration']
    pupiltime = pupildf[pupilcols]
    pupiltime.rename(columns={"Subject ID":"vetsaid"}, inplace=True)
    pupiltime.loc[:,'Date'] = pd.to_datetime(pupiltime['Date'])
    return pupiltime


def get_behav_times(behavdf):
    """Get timestamp and date info from behavioral file. Converts from wide to long 
    with a column indicating the trial each timestamp is associated with."""
    # Select columns with timestamp info
    timecols = [col for col in behavdf.columns if "TIM" in col]
    behavdf = behavdf[["SUBJECTID","TESTDATE"]+timecols]
    behavdf.rename(columns={"SUBJECTID":"vetsaid", "TESTDATE":"Date"}, inplace=True)
    # Rotate variable names to make it easier to go from wide format to long
    behavdf.columns = [rotate(col, -3) if col in timecols else col for col in behavdf.columns]
    # Convert from wide to long format
    behavdflong = pd.wide_to_long(behavdf, stubnames="TIM", i="vetsaid", j="Trial", suffix="[a-zA-Z0-9_]").reset_index()
    behavdflong['TIM'].replace(999999,np.nan, inplace=True)
    behavdflong = behavdflong.dropna(axis=0)    
    # Get rid of decimal and convert to string
    behavdflong['TIM'] = behavdflong['TIM'].astype(str).str.replace("\.0","").str.zfill(6)
    # Convert to timestamp
    behavdflong['Time'] = behavdflong['TIM'].str[:2] + ":" + behavdflong['TIM'].str[2:4] + ":" + behavdflong['TIM'].str[4:]
    behavdflong["Date"] = behavdflong["Date"].str.split(":").str[0]
    behavdflong["Date"] = pd.to_datetime(behavdflong.Date, format='%d%b%Y')
    behavtime = behavdflong.drop(columns='TIM')
    return behavtime


def main(indir, behav, outdir):
    # Get pupillometer timestamp data
    pupilfiles = get_pupil_files(indir)
    pupildf = merge_parsed_files(pupilfiles)
    pupiltime = get_pupil_times(pupildf)
    # Get database timestamp data
    behavdf = pd.read_csv(behav)
    behavtime = get_behav_times(behavdf)
    # Full merge on Subject, Date, and Time. 
    fulldf = pd.merge(pupiltime, behavtime, on=['vetsaid','Date','Time'], how='outer', indicator=True)
    fulldf.rename(columns={"_merge":"MatchResult"}, inplace=True)
    # Indicate whether timestamp is matched, and if not, which source it came from
    fulldf['MatchResult'] = fulldf['MatchResult'].str.replace('left_only','db_missing')
    fulldf['MatchResult'] = fulldf['MatchResult'].str.replace('right_only','pupil_missing')
    fulldf['MatchResult'] = fulldf['MatchResult'].str.replace('both','complete')
    fulldf.sort_values(['vetsaid','Time'], inplace=True)
    # Indicate whether subject is present in both data sources. May not have been entered or backed up yet.
    completesubs = np.intersect1d(pupiltime.vetsaid.unique(), behavtime.vetsaid.unique())
    fulldf["SubjectEntry"] = "Partial"
    fulldf.loc[fulldf.vetsaid.isin(completesubs),"SubjectEntry"] = "Complete"
    # Save out file of unmatched timestamps
    missingdf = fulldf[fulldf.MatchResult!="complete"]
    missingdf = missingdf[missingdf.SubjectEntry=="Complete"]
    timestamp = datetime.now().strftime("%Y%m%d")
    fname = "UnmatchedTimestamps_" + timestamp + ".csv"
    outfile = os.path.join(outdir, fname)
    try:
        missingdf.to_csv(outfile, index=False)
        print "Missing timestamp list saved successfully" 
    except IOError:
        print "Missing timestamp list could not be saved"
        
        
    
if __name__ == '__main__':

    root = Tkinter.Tk()
    root.withdraw()

    # Select parsed pupil data files
    indir = tkFileDialog.askdirectory(parent=root,initialdir=os.getcwd(),
                                      title='Please select input directory containing parsed pupil data')
    # Select file with behavioral info
    behav = tkFileDialog.askopenfilename(parent=root,
                                         title='Choose behavioral performance file')    
    # Select output directory to save out to
    outdir = tkFileDialog.askdirectory(parent=root,initialdir=os.getcwd(), 
                                       title='Please select output directory')
    # Run script
    main(indir, behav, outdir)
    