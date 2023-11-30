# -*- coding: utf-8 -*-
"""
Created on Fri Dec  2 14:08:17 2016

@author: jelman
"""

import os, sys
import pandas as pd
import numpy as np
import argparse
import string
from datetime import datetime
import itertools
import Tkinter,tkFileDialog

def rotate(strg,n):
    """ Create function to rotate characters in a string from front to back"""
    return strg[n:] + strg[:n]


def proc_behav(behav_file):
    # Load behavioral data with trial times and scan quality
    behavdf = pd.read_csv(behav_file, sep=",")
    behavdf.columns = behavdf.columns.str.replace("_v2","")
    if 'DSTIM' in behavdf.columns:
        behavdf = behavdf.drop("DSTIM", 1)
    if 'SUBJECTID' in behavdf.columns:
        behavdf.rename(columns={"SUBJECTID":"vetsaid"}, inplace=True)
    # Select columns of interest
    lrtcols = [col for col in behavdf.columns if ("LRT" in col) & (("SCN" in col) or ("TIM" in col))]
    behavdf = behavdf[["vetsaid", "ZPUPILLR"]+lrtcols]
    # Rotate variable names to make it easier to go from wide format to long
    behavdf.columns = [rotate(col, -3) if col in lrtcols else col for col in behavdf.columns]
    behavdf.columns = behavdf.columns.str.replace("LRT","PLR")
    # Convert from wide to long format
    behavdflong = pd.wide_to_long(behavdf, stubnames=["TIM","SCN"], i="vetsaid", j="Trial #").reset_index()
    behavdflong['TIM'].replace("999999",np.nan, inplace=True)
    behavdflong['SCN'].replace("9",np.nan, inplace=True)
    # Strip string from trial number and convert to int so it will sort in numerical order
    behavdflong["Trial #"] = behavdflong["Trial #"].str.replace("PLR","").astype(int)
    # Sort by subject id
    behavdflong = behavdflong.sort_values(by=["vetsaid","Trial #"])
    # Rename subject ID field
    behavdflong = behavdflong.rename(columns={"vetsaid":"ID"})
    # Get rid of decimal and convert to string
    behavdflong['TIM'] = behavdflong['TIM'].astype(str).str.replace("\.0","").str.zfill(6)
    # Convert to timestamp
    behavdflong.ix[behavdflong['TIM'].str.contains("nan"),'TIM'] = np.nan
    behavdflong['Pupil Trial Time'] = behavdflong['TIM'].str[:2] + ":" + behavdflong['TIM'].str[2:4] + ":" + behavdflong['TIM'].str[4:]
    # Create Task field
    behavdflong['Task (PLR)'] = 'PLR' + behavdflong['Trial #'].astype(str)
    # Make sure all subjects have 10 rows
    assert (behavdflong.groupby('ID')['ID'].count()==10).all()
    # Specify bad data trials and filter out unacquired trials
    behavdflong = behavdflong.dropna(axis=0, subset=["Pupil Trial Time"])
    behavdflong = behavdflong.loc[(behavdflong['SCN']==1) & (behavdflong['ZPUPILLR']<=2)]
    bxtrialnames = behavdflong.groupby('ID').apply(lambda subdf: [''.join(['S',str(i)]) for i in list(string.lowercase[:subdf.shape[0]])])
    behavdflong['Bx Trial'] = list(itertools.chain.from_iterable(bxtrialnames))
    return behavdflong


def merge_parsed_files(infiles):
    pupildf_list = []
    for infile in infiles:
        # Load parsed pupil data
        subjdf = pd.read_csv(infile, sep=",")
        # Append to list
        pupildf_list.append(subjdf)
    # Merge individual files
    pupildf = pd.concat(pupildf_list)
    return pupildf


def proc_pupil_data(pupildf):
    if '0.000000000' in pupildf.columns:
        pupildf.rename(columns={'0.000000000':'0'}, inplace=True)   
    # Calculate Min and Max fields
    # Insert min
    pupildf.insert(pupildf.columns.get_loc("0"), 'Min', pupildf.ix[:,'0':].min(axis=1))
    # Insert max
    pupildf.insert(pupildf.columns.get_loc("0"), 'Max', pupildf.ix[:,'0':].max(axis=1))
    # Rename columns
    pupildf = pupildf.rename(columns={"Subject ID":"ID", "Eye Measured":"LR", "Time":"Pupil Trial Time"})
    ndatacols = pupildf.columns[pupildf.columns.get_loc("0"):].shape[0]
    datacolnames = [str(x +1) + 'st data pt' for x in range(ndatacols)]
    pupildf.columns = list(pupildf.columns[:pupildf.columns.get_loc("0")]) + datacolnames
    return pupildf, datacolnames
    
    
def main(outdir, behav, infiles):
    # Process behavioral data
    behavdflong = proc_behav(behav)
    # Merge all parsed pupil files
    pupildf = merge_parsed_files(infiles)
    # Process pupil data
    procpupildf, datacolnames = proc_pupil_data(pupildf)    
    # Merge data
    mergeddf = behavdflong.merge(procpupildf, how="inner", on=["ID","Pupil Trial Time"])
    # Select columns
    templatePLR = mergeddf[['ID','Task (PLR)','Pupil Trial Time','Trial #', 
                           'Bx Trial','Min','Max']+datacolnames]
    # Save out template file
    timestamp = datetime.now().strftime("%Y%m%d")
    fname = 'PLR_Template_' + timestamp + '.xlsx'
    outfile = os.path.join(outdir, fname)
    templatePLR.to_excel(outfile, index=False)

if __name__ == '__main__':

    root = Tkinter.Tk()
    root.withdraw()

    # Select parsed pupil data files
    infiles = tkFileDialog.askopenfilenames(parent=root,title='Choose parsed pupil data files')
    infiles = list(infiles)
    # Select file with behavioral info
    behav = tkFileDialog.askopenfilename(parent=root,title='Choose behavioral performance file')    
    # Select output directory to save out to
    outdir = tkFileDialog.askdirectory(parent=root,initialdir=os.getcwd(), title='Please select output directory')
    # Run script
    main(outdir, behav, infiles)

    # parser = argparse.ArgumentParser(description="""This is a script to create template file for Digit Span processing.""")
    # parser.add_argument('-o', '--outdir', type=str, required=True,
    #                     help='Directory to save output file.')
    # parser.add_argument('-b', '--behav', type=str, required=True,
    #                 help='File containing behavioral and accuracy info.')
    # parser.add_argument('-i','--infiles', nargs='+', help='List of parsed input files', required=True)

    # if len(sys.argv) == 1:
    #     parser.print_help()
    # else:
    #     args = parser.parse_args()
    #     ### Begin running script ###
    #     main(args.outdir, args.behav, args.infiles)

