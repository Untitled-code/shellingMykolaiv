#!/home/investigator/EnvPy/jupyter_venv/bin/python
# coding: utf-8
import os
from pathlib import Path
import csv
from time import strptime
import pandas as pd
from geojson import Feature, FeatureCollection, Point
import json

PATH = './'
files = []
concatenated = pd.DataFrame() #create empty dataframe
def date_convert(df): # froming date and unix timestamp columns
    for i in range(len(df)):
        month = df['month'][1]
        s = month.strip()[:3] #strip to 3 letter
        m = strptime(s,'%b').tm_mon #getting month number
        print(m)
        time = (f"2022-{m}-{df['day'][i]}")
        print(time)
        df.loc[i, ['date']] = time
        time_ms = pd.Timestamp(time).timestamp()
        df.loc[i,['timestamp']] = time_ms*1000 #converting to miliseconds

for filename in os.listdir(PATH):
    if filename.endswith('xlsx'):
        print(filename)
        files.append(filename)
print(files)
for filepath in files:
    print(f'Working with ...{filepath}')
    workbook = pd.ExcelFile(filepath)
    sheets = workbook.sheet_names
    # creating dataframe from file xlsx
    df = pd.concat([pd.read_excel(workbook, sheet_name=s)
                    .assign(sheet_name=s) for s in sheets], ignore_index=True)
    df[['la', 'lo']] = df['coordinates'].str.split(',', 1, expand=True) #split column coordinates into two
    del(df['coordinates']) #deleting coordinates column
    # del(df['type']) #deleting type column
    df['la'] = df['la'].astype(float) #assigning float to la and lo column
    df['lo'] = df['lo'].astype(float)
    print(df)
    df = df.dropna(subset=['day'])  # dropping all Null values in column
    df['day'] = df['day'].astype(int)
    date_convert(df)
    del(df['day'])
    del(df['month'])
    concatenated = pd.concat([concatenated, df])  # concate multiple tables into one
del (concatenated['type'])
del (concatenated['Unnamed: 3'])
concatenated['timestamp'] = concatenated['timestamp'].astype(int) #making timestamp integer
concatenated.to_csv('total.csv', index=False) #saving full table

"""splitting database into two"""
df1 = concatenated.loc[concatenated['description'].isnull()] #show empty rows
df2 = concatenated.loc[concatenated['description'].notnull()] #show without rows
del (df1['description']) #deleting description column because it is empty
del (df1['scale']) #deleting scale column because it is empty
df1.to_csv('df1.csv', index=False) #saving 1 table
df2.to_csv('df2.csv', index=False) #saving 2 table
"""Converting into geojson"""

# from here https://notebook.community/captainsafia/nteract/applications/desktop/example-notebooks/pandas-to-geojson
def df_to_geojson(df, properties, lat='la', lon='lo'):
    # create a new python dict to contain our geojson data, using geojson format
    geojson = {'type':'FeatureCollection', 'features':[]}

    # loop through each row in the dataframe and convert each row to geojson format
    for _, row in df.iterrows():
        # create a feature template to fill in
        feature = {'type':'Feature',
                   'properties':{},
                   'geometry':{'type':'Point',
                               'coordinates':[]}}

        # fill in the coordinates
        feature['geometry']['coordinates'] = [row[lon],row[lat]]

        # for each column, get the value and add it as a new feature property
        for prop in properties:
            feature['properties'][prop] = row[prop]
        
        # add this feature (aka, converted dataframe row) to the list of features inside our dict
        geojson['features'].append(feature)
    
    return geojson


cols1 = ['sheet_name', 'date','timestamp']
cols2 = ['sheet_name','scale','description','date','timestamp']

geojson1 = df_to_geojson(df1, cols1)
geojson2 = df_to_geojson(df2, cols2)
with open(f'data1.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson1, f, ensure_ascii=False)
with open(f'data2.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson2, f, ensure_ascii=False)
