# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 12:49:05 2016

@author: jelman
"""
import re
import os
import itertools
import pandas as pd
import numpy as np

# Open file and read lines
filename = '/home/jelman/netshare/K/data/Pupillometry/VETSA3/testing/19089A Pupillometry Data.txt'
with open(filename, 'r') as f:
    lines = f.readlines()
    
# Strip newlines characters    
newlines = [line.replace('\r\n', '') for line in lines]
# Delete redundant 75% recovery time value reported on same line as latency
newlines = [re.sub(', 75%.*', '', line) for line in newlines]


### Join multi-line elements ###


# Add blank space to end so that loop will include last element in list
newlines.append('')
# Create iterator 
iterlines = iter(newlines)
# Initialize results container
results = []
# Initialize previous line variable
prev = next(iterlines)
# Begin looping. Join multi-line elements and place breakpoints between trials
for line in iterlines:
    if re.search("= $", prev):
        results.append(prev+line)
        prev = next(iterlines)
    elif (prev=='' and line==''):
        results.append('BREAK')
        prev = next(iterlines)
        continue
    else:
        results.append(prev)
        prev = line

# Break list into sublists of trials
sublists = [list(x[1]) for x in itertools.groupby(results, lambda x: x=='BREAK') if not x[0]]


### Create separate sublists for digit span and pupil light reflex data ###

# Initialize list for digit span data and pupil light reflex
sublistsDS = []
sublistsPLR = []

# Append data to digit span and pupil light reflex lists
for sublist in sublists:
    if  'Measurement Duration = 15.000sec' in sublist:
        sublistsDS.append(sublist)
    elif 'Measurement Duration = 5.000sec' in sublist:
        sublistsPLR.append(sublist)
    else:
        continue

# Create pandas dataframe from digit span sublists    
dictDSlist = []
for sublistDS in sublistsDS:
    dictDS = {}
    for item in sublistDS:
        key, val = item.split(' = ')
        dictDS[key.strip()] = val.strip()
    dictDSlist.append(dictDS)
dfDS_all = pd.DataFrame(dictDSlist)
    
# Create pandas dataframe from pupil light reflex sublists    
dictPLRlist = []
for sublistPLR in sublistsPLR:
    dictPLR = {}
    for item in sublistPLR:
        key, val = item.split(' = ')
        dictPLR[key.strip()] = val.strip()
    dictPLRlist.append(dictPLR)
dfPLR_all = pd.DataFrame(dictPLRlist)

### Save out data ###

# Digit span: Keep columns of interest and save out rest
dfDS_all.Time = pd.to_datetime(dfDS_all.Time)
dsCols = ['Subject ID', 'Time', 'Device ID', 'Eye Measured', 'Record ID', 
          'Profile Normal', 'Diameter', 'Measurement Duration', 
          'Pupil Profile']
dfDS = dfDS_all[dsCols]
dfDS = dfDS.sort_values(by='Time').reset_index(drop=True)
# Save out full dataset
outfile = os.path.splitext(filename)[0].replace(' Pupillometry Data','_DS_Data.csv')
dfDS.to_csv(outfile, index=False)

# Pupil light reflex: Keep columns of interest and save out rest
dfPLR_all.Time = pd.to_datetime(dfPLR_all.Time)
plrCols = ['Subject ID', 'Time', 'Device ID', 'Eye Measured', 'Record ID', 
          'Profile Normal', 'Diameter', 'Measurement Duration', 'Mean/Max C. Vel', 
          'dilation velocity', 'Lat', '75% recovery time', 'Pupil Profile']
dfPLR = dfPLR_all[plrCols]
dfPLR = dfPLR.sort_values(by='Time').reset_index(drop=True)
# Save out full dataset
outfile = os.path.splitext(filename)[0].replace(' Pupillometry Data','_PLR_Data.csv')
dfPLR.to_csv(outfile, index=False)

### Create dataframe according to template needed to matlab processing ###

# Initialize digit span dataframe
templateDS = pd.DataFrame({"ID": dfDS['Subject ID'],
                           "Task (DS)": ['DS'+str(x+1) for x in range(dfDS.shape[0])],
                           "Time": dfDS['Time'],
                           "Trial #": range(1, dfDS.shape[0]+1),
                           "Bx Trial": "",
                           "Min": np.nan,
                           "Max": np.nan,
                           "Pupil Profile": dfDS['Pupil Profile']},
                           columns=['ID','Task (DS)','Time','Trial #','Bx Trial',
                                    'Min','Max','Pupil Profile'])
pprofileDS = templateDS.pop('Pupil Profile').str.split('\t', expand=True)
pprofileDS = pprofileDS.rename(columns=lambda x: str(x+1) + 'st data pt')
templateDS = pd.concat([templateDS,pprofileDS], axis=1)
templateDS['Min'] = templateDS.ix[:,'1st data pt':].min(axis=1, skipna=True)
templateDS['Max'] = templateDS.ix[:,'1st data pt':].max(axis=1, skipna=True)

# Save out data according to template. Still needs good/bad trials marked 
outfile = os.path.splitext(filename)[0].replace(' Pupillometry Data','_DS_raw.csv')
templateDS.to_csv(outfile, index=False)
