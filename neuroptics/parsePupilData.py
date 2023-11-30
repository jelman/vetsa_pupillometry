# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 10:24:32 2016

@author: jelman
"""

import re
import os, sys
import itertools
import pandas as pd
import numpy as np
from datetime import datetime
import Tkinter,tkFileDialog

def read_file(filename):
# Open file and read lines
    with open(filename, 'r') as f:
        lines = f.readlines()
    return lines


def clean_text(lines):
    # Strip newlines characters
    newlines = [line.replace('\r\n', '') for line in lines]
    newlines = [line.replace('\n', '') for line in newlines]
    # Delete redundant 75% recovery time value reported on same line as latency
    newlines = [re.sub(', 75%.*', '', line) for line in newlines]
    if newlines[0] == '':
        newlines.pop(0)
    return newlines

def multi_delete(list_, indexes):
    indexes = sorted(list(indexes), reverse=True)
    for index in indexes:
        del list_[index]
    return list_

def join_multilines(lines):
    break_idx = [ i for i, item in enumerate(lines) if item.endswith("= ") ]
    for i in break_idx:
        lines[i] = ''.join(lines[i:i+2])
    del_idx = [x+1 for x in break_idx]
    lines = multi_delete(lines, del_idx)
    return lines
    
def split_trial_lists(lines):
    # Break list into sublists of trials
    sublists = [list(x[1]) for x in itertools.groupby(lines, lambda x: x=='') if not x[0]]
    return sublists

def get_task_lists(trial_lists):
    # Initialize list for digit span data and pupil light reflex
    sublistsDS = []
    sublistsPLR = []
    sublistsCFREC = []
    # Append data to digit span and pupil light reflex lists
    for sublist in trial_lists:
        if  'Measurement Duration = 15.000sec' in sublist:
            sublistsDS.append(sublist)
        elif 'Measurement Duration = 5.000sec' in sublist:
            sublistsPLR.append(sublist)
        elif 'Measurement Duration = 25.000sec' in sublist:
            sublistsCFREC.append(sublist)
        else:
            continue
    return sublistsPLR, sublistsDS, sublistsCFREC

def create_plr_df(sublistsPLR):
    dictPLRlist = []
    for sublistPLR in sublistsPLR:
        dictPLR = {}
        for item in sublistPLR:
            key, val = item.split(' = ')
            dictPLR[key.strip()] = val.strip()
        dictPLRlist.append(dictPLR)
    plr_df = pd.DataFrame(dictPLRlist)
    return plr_df


def create_task_df(sublistsTask):
    # Create pandas dataframe from task sublists
    dictTasklist = []
    for tasklist in sublistsTask:
        dictTask = {}
        for item in tasklist:
            if item == '':
                continue
            else:
                key, val = item.split(' = ')
                dictTask[key.strip()] = val.strip()
        dictTasklist.append(dictTask)
    task_df = pd.DataFrame(dictTasklist)
    return task_df


def get_subid(df):
    try:
        assert len(df['Subject ID'].unique())==1
        return df['Subject ID'][0]
    except AssertionError:
        print "Found multiple subject IDs in file: %s" % ', '.join(df['Subject ID'].unique())
    
    
def sort_time(df, timevar):
    df[timevar] = pd.to_datetime(df[timevar])
    df = df.sort_values(by=timevar).reset_index(drop=True)
    return df
   

def create_plr_file(dfraw):
    plrCols = ['Subject ID', 'Time', 'Device ID', 'Eye Measured', 'Record ID',
      'Profile Normal', 'Diameter', 'Measurement Duration', 'Mean/Max C. Vel',
      'dilation velocity', 'Lat', '75% recovery time', 'Pupil Profile']
    df = dfraw[plrCols]
    pprofile = df.pop('Pupil Profile').str.split('\t', expand=True)
    ntimepoints = len(dfraw.loc[dfraw.index[0],'Time Profile'].split('\t'))
    assert ntimepoints == 150
    pprofile.columns = dfraw.loc[dfraw.index[0],'Time Profile'].split('\t')
    df = pd.concat([df,pprofile], axis=1)
    df[['Date','Time']] = df['Time'].astype(str).str.split(' ',expand=True) 
    return df
    
def create_task_file(dfraw):
    df = dfraw[['Subject ID','Time','Profile Normal','Device ID','Record ID',
            'Eye Measured','Pulse Intensity','DC Intensity','Pulse Start Time',
            'Pulse Duration','Measurement Duration','Pupil Profile']]
    pprofile = df.pop('Pupil Profile').str.split('\t', expand=True)
    ntimepoints = len(dfraw.loc[dfraw.index[0],'Time Profile'].split('\t'))
    assert (ntimepoints == 450) | (ntimepoints == 750)
    pprofile.columns = dfraw.loc[dfraw.index[0],'Time Profile'].split('\t')
    df = pd.concat([df,pprofile], axis=1)
    df[['Date','Time']] = df['Time'].astype(str).str.split(' ', expand=True)
    return df


def parse_PLR(sublistsPLR):
    """Parse pupil light reflex data."""
    plr_df = create_plr_df(sublistsPLR)
    plr_df.columns = plr_df.columns.str.replace('C. Lat', 'Lat')
    plr_df = sort_time(plr_df, 'Time')
    plr_data = create_plr_file(plr_df)
    return plr_data


def parse_DS(sublistsDS):
    ds_df = create_task_df(sublistsDS)
    ds_df = sort_time(ds_df, 'Time')
    ds_data = create_task_file(ds_df)
    return ds_data
    

def parse_CFREC(sublistsCFREC):
    cfrec_df = create_task_df(sublistsCFREC)
    cfrec_df = sort_time(cfrec_df, 'Time')
    cfrec_data = create_task_file(cfrec_df)
    return cfrec_data


def parse_pupil_data(filelist, outdir):
    for filename in filelist:
        rawlines = read_file(filename)
        clean_lines = clean_text(rawlines)
        joined_lines = join_multilines(clean_lines)
        trial_lists = split_trial_lists(joined_lines)
        sublistsPLR, sublistsDS, sublistsCFREC = get_task_lists(trial_lists)
        timestamp = datetime.now().strftime("%Y%m%d")
        # Pupil Light Reflex
        if len(sublistsPLR) > 0:
            plr_data = parse_PLR(sublistsPLR)
            subid = get_subid(plr_data)
            plrfname = subid + '_Pupil_PLR_Parsed_' + timestamp + '.csv'
            plroutfile = os.path.join(outdir, plrfname)
            try:
                plr_data.to_csv(plroutfile, index=False)
                print "PLR file for %s saved successfully" %(subid)
            except IOError:
                print "PLR file for %s could not be saved" %(subid)
        # Digit Span
        if len(sublistsDS) > 0:
            ds_data = parse_DS(sublistsDS)
            subid = get_subid(ds_data)
            dsfname = subid + '_Pupil_DS_Parsed_' + timestamp + '.csv'
            dsoutfile = os.path.join(outdir, dsfname)
            try:
                ds_data.to_csv(dsoutfile, index=False)
                print "DS file for %s saved successfully" %(subid)
            except IOError:
                print "DS file for %s could not be saved" %(subid)
        # Category Fluency and Recognition
        if len(sublistsCFREC) > 0:
            cfrec_data = parse_CFREC(sublistsCFREC)
            subid = get_subid(cfrec_data)
            cfrecfname = subid + '_Pupil_CFREC_Parsed_' + timestamp + '.csv'
            cfrecoutfile = os.path.join(outdir, cfrecfname)
            try:
                cfrec_data.to_csv(cfrecoutfile, index=False) 
                print "CFREC file for %s saved successfully" %(subid)
            except IOError:
                print "CFREC file for %s could not be saved" %(subid)
            

if __name__ == '__main__':

    root = Tkinter.Tk()
    root.withdraw()
    # Select files to parse
    filelist = tkFileDialog.askopenfilenames(parent=root,title='Choose files to parse')
    filelist = list(filelist)
    # Select output directory to save out to
    outdir = tkFileDialog.askdirectory(parent=root,initialdir=os.getcwd(), title='Please select output directory')
    # Run script
    parse_pupil_data(filelist, outdir)
