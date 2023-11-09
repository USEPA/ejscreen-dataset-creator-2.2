#****************************************************************************************
# Name:        EJScreenTool
# Purpose:     Provide a group of functions to automate the creation of the EJScreen dataset
#
# Author:      SAIC, EPA OMS Contractor
#
# Created:     08/31/2023
# Updated:     08/31/2023
# 
# imports:
#   pandas: pandas dataframes provide a simple and easy way to read the input data and build the new EJScreen tables
#   numpy: numpy functions are used to generate percentiles for the lookup tables
#   col_names: a python file containing lists that together comprise all of the columns in teh EJScreen dataset
#   warnings: used to disable 2 specific warning messages that would otherwise be output to the console hundreds of times. Warnings being ignored are:
#       1. Letting us know when an entire column in percentile calculationis NA. 
#       2. Pandas making suggestions on how to accomplish a certain task.
#   math: Used to determine if a value is not a number. 
#   os.path: Used to get directory when exporting spatial dataset
#   arcgis: required to import feature class as a pandas dataframe. This package is only imported if you attempt to export the dataset to an ESRI feature class.
#   arcpy: Batch Update Field tool is used to set field order, datatypes, and aliases of final feature class. This package is only imported if you attempt to export the dataset to an ESRI feature class.
#
#****************************************************************************************


import pandas as pd 
import numpy as np
import col_names
import warnings
import math
import os.path
#import arcpy
#from arcgis import GeoAccessor, GeoSeriesAccessor

#-------------------------------------------------------------------------------
# Name:        ejscreen_cal
# Purpose:     Build EJScreen dataset using US based percentiles.
# 
# Parameters:
#   input_csv - path to csv file containing EJScreen indicator data and ID
#   output_csv - path to output csv that will contain EJScreen dataset.
#   output_lookup - path to output xlsx that will contain the percentile lookup table
#   to_featureclass - (True/False) whether or not the EJScreen dataset will be joined to geometry and output to a file geodatabase
#   geom_source = path to featureclass containing geometry that will be joined to the EJScreen dataset. 
#   output_fc = path to output EJScrfeen featureclass 
#   schema = path to csv file containing field update schema. Format can be found here: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/batch-update-fields.htm
#   
#   col_names.py will need to be up to date for all fields to be processed correctly. 
#-------------------------------------------------------------------------------

def ejscreen_cal(input_csv, output_csv, output_lookup, to_featureclass = False, geom_source = "", output_fc = "", schema = ""):

    #eliminates warnings that have no effect on results
    warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) 
    warnings.filterwarnings("ignore", message="All-NaN slice encountered")

    #import dataset
    source_df = pd.read_csv(input_csv, usecols=(col_names.info_names + col_names.data_names), dtype= {"ID": str})

    #import extra fields to add back at end
    if len(col_names.extra_cols) > 0:
        extra_df = pd.read_csv(input_csv, usecols=col_names.extra_cols) 

    #calculate percentiles for socioeconomic and pollution & sources
    indicator_pctiles, indicator_lookup = percentileCal(source_df, output = False) 

    #calculate raw EJ index and Supplemental index values
    indicator_indexes = calIndexes(indicator_pctiles) 

    #calculate percentiles for EJ & Supplemental indexes
    ejscreen_pctiles, index_lookup = percentileCal(indicator_indexes, output=False, percentile_column_names = col_names.index_names) 
    
    #calcualte B_ and T_ fields
    ejscreen_full = calBinTxt(ejscreen_pctiles, output=False) 

    #add extra columns back in
    if len(col_names.extra_cols) > 0:
        ejscreen_full = pd.concat([ejscreen_full, extra_df], axis=1) 

    index_names_2f = [i for i in col_names.index_names if i.startswith('P_D2_')]
    index_names_5f = [i for i in col_names.index_names if i.startswith('P_D5_')]

    #count how many 2 factor EJ Indexes exceed the 80th percentile
    ejscreen_full['EXCEED_COUNT_80'] = ejscreen_full[index_names_2f].ge(80).sum(axis=1) 
    
    #count how many 5 factor EJ Indexes exceed the 80th percentile
    ejscreen_full['EXCEED_COUNT_80_SUPP'] = ejscreen_full[index_names_5f].ge(80).sum(axis=1) 
    
    #combine the two lookup tables
    ejscreen_lookup = pd.concat([indicator_lookup, index_lookup], axis=1)

    #put columns in correct order
    ejscreen_full = ejscreen_full[col_names.cols_all] 
        
    ejscreen_full.to_csv(output_csv)
    ejscreen_lookup.to_excel(output_lookup)

    if to_featureclass == True:
        exportSpatial(geom_source, ejscreen_full, output_fc, schema)


#-------------------------------------------------------------------------------
# Name:        ejscreenState_cal
# Purpose:     Build EJScreen dataset using state based percentiles.
# 
# Parameters:
#   input_csv - path to csv file containing EJScreen indicator data and ID
#   output_csv - path to output csv that will contain EJScreen dataset.
#   output_lookup - path to output xlsx that will contain the percentile lookup table
#   to_featureclass - (True/False) whether or not the EJScreen dataset will be joined to geometry and output to a file geodatabase
#   geom_source = path to featureclass containing geometry that will be joined to the EJScreen dataset. 
#   output_fc = path to output EJScrfeen featureclass 
#   schema = path to csv file containing field update schema. Format can be found here: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/batch-update-fields.htm
#   
#   col_names.py will need to be up to date for all fields to be processed correctly. 
#-------------------------------------------------------------------------------


def ejscreenState_cal(input_csv, output_csv, output_lookup, to_featureclass = False, geom_source = "", output_fc = "", schema = ""):
     
    #eliminates a warning that has no effect on results
    warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) 
    #eliminates a warning that has no effect on results
    warnings.filterwarnings("ignore", message="All-NaN slice encountered")

    #these imports are done here to allow for users without an ArcGIS Pro installation to still generate the csv dataset
    if to_featureclass == True:
        import arcpy
        from arcgis import GeoAccessor, GeoSeriesAccessor

    #import dataset
    source_df = pd.read_csv(input_csv, usecols=(col_names.info_names + col_names.data_names), dtype= {"ID": str})  

    #import extra fields to add back at end
    if len(col_names.extra_cols) > 0:
        extra_df = pd.read_csv(input_csv, usecols=col_names.extra_cols) 

    #calculate percentiles for socioeconomic and pollution & sources
    indicator_pctiles, indicator_lookup = percentileCalState(source_df, output = False) 

    #calculate raw EJ index and Supplemental index values
    indicator_indexes = calIndexes(indicator_pctiles) 

    #calculate percentiles for EJ & Supplemental indexes
    ejscreen_pctiles, index_lookup = percentileCalState(indicator_indexes, output=False, percentile_column_names = col_names.index_names) 
    
    #calcualte B_ and T_ fields
    ejscreen_full = calBinTxt(ejscreen_pctiles, output=False) 

    #add extra columns back in
    if len(col_names.extra_cols) > 0:
        ejscreen_full = pd.concat([ejscreen_full, extra_df], axis=1) 

    #get 2 factor percentile columns
    index_names_2f = [i for i in col_names.index_names if i.startswith('P_D2_')] 
    
    #get 5 factor percentiles columns
    index_names_5f = [i for i in col_names.index_names if i.startswith('P_D5_')] 

    #count how many 2 factor EJ Indexes exceed the 80th percentile
    ejscreen_full['EXCEED_COUNT_80'] = ejscreen_full[index_names_2f].ge(80).sum(axis=1) 
    
    # count how many 5 factor EJ Indexes exceed the 80th percentile
    ejscreen_full['EXCEED_COUNT_80_SUPP'] = ejscreen_full[index_names_5f].ge(80).sum(axis=1) 

    
    #combines the indicators lookup with the indexes lookup
    ejscreen_lookup = pd.concat([indicator_lookup, index_lookup.drop(["PCTILE", "REGION"], axis = 1)], axis=1) 

    #removes the percentile column
    ejscreen_lookup = ejscreen_lookup.drop(['PCTILE'], axis = 1) 

    #sets the index as the percentile column
    ejscreen_lookup.index.name='PCTILE' 

    #put columns in correct order
    ejscreen_full = ejscreen_full[col_names.cols_all] 
    
    ejscreen_full.to_csv(output_csv)
    ejscreen_lookup.to_excel(output_lookup)

    if to_featureclass == True:
        exportSpatial(geom_source, ejscreen_full, output_fc, schema)

#-------------------------------------------------------------------------------
# Name:        percentileCal
# Purpose:     Calculate percentile fields and create lookup table at the national level. 
# 
# Parameters:
#   ejscreen_data_df - dataframe containing EJScreen raw data. Must at least contain the columns designated by column_names parameter
#   output_csv_percentiles - path to output csv that will contain EJScreen dataset
#   output_xlsx_lookup - path to output xlsx that will contain the percentile lookup table
#   output - (True/False) whether or not data will be written to csv and excel file respectively
#   column_names = list containing the columns for which percentiles will be calculated
#-------------------------------------------------------------------------------

def percentileCal(ejscreen_data_df, output_csv_percentiles = "", output_xlsx_lookup = "", output = False, percentile_column_names = col_names.data_names): 

     #create list of percentiles
     pct_list = np.arange(0,101) 

     #create empty lookup table with percentile column
     lookup = pd.DataFrame(pct_list, columns=["PCTILE"]) 

     #change PCTILE column to string so "mean" can be added later
     lookup = lookup.astype(str) 

     #set PCTILE as the index so you dont output an extra column
     lookup = lookup.set_index(['PCTILE']) 

     #generate statistics for every column
     desc = ejscreen_data_df[percentile_column_names].describe() 
     
     #extract mean for every column from stats
     means = desc.iloc[[1]] 
     
     for col in percentile_column_names:
          print(col)
          
          #Create lookup table

          #find the value of every percentile from 0-100 ignoring NA values
          lookup[col]= np.nanpercentile(ejscreen_data_df[col], pct_list) 
          
          #format lookup for next step
          lookupList = (lookup[col].values.tolist()) 
          
          #Calculate EJScreen Percentiles
          ejscreen_data_df[("P_" + col)] = ejscreen_data_df[col].apply(lambda x: getPctile(lookupList, x))

     #append means to lookup table     
     lookup = pd.concat([lookup, means], axis = 0) 

     #update field name that doesnt follow naming convention
     if "P_PRE1960PCT" in ejscreen_data_df.columns:   
        ejscreen_data_df.rename(columns={"P_PRE1960PCT":"P_LDPNT"}, inplace = True) 

     #if true, output to excel and csv respectively
     if(output == True): 
          lookup.to_excel(output_xlsx_lookup)
          ejscreen_data_df.to_csv(output_csv_percentiles)

     return(ejscreen_data_df, lookup)


#-------------------------------------------------------------------------------
# Name:        percentileCalState
# Purpose:     Calculate percentile fields and create lookup table at the state level. 
# 
# Parameters:
#   ejscreen_data_df - dataframe containing EJScreen raw data. Must at least contain the columns designated by column_names parameter
#   output_csv_percentiles - path to output csv that will contain EJScreen dataset
#   output_xlsx_lookup - path to output xlsx that will contain the percentile lookup table
#   output - (True/False) whether or not data will be written to csv and excel file respectively
#   column_names = list containing the columns for which percentiles will be calculated
#-------------------------------------------------------------------------------


def percentileCalState(ejscreen_data_df, output_csv_percentiles = "", output_xlsx_lookup = "", output = False, percentile_column_names = col_names.data_names): 
    
     #create a copy of the input data. The percentiles will be appended to this at the end. 
     final_df = ejscreen_data_df.copy() 

     #generate list of percentiles
     pct_list = np.arange(0,101) 

     #create empty dataframe that state lookup tables will be copied into
     lookup = pd.DataFrame() 

     print("Generating Lookup Table...")
     for state in pd.unique(ejscreen_data_df['ST_ABBREV']):

          #create temp lookup table for state
          temp_lookup = pd.DataFrame(pct_list, columns = ["PCTILE"]) 

          #set region column to the state name
          temp_lookup['REGION'] = state 

          #create dataframe of only the data of the state being operated on
          state_data = ejscreen_data_df[ejscreen_data_df['ST_ABBREV'] == state] 

          #generate statistics for columns in state dataset
          desc = state_data[percentile_column_names].describe() 

          #extract mean for every column from stats
          means = desc.iloc[[1]] 

          for col in percentile_column_names:
               
               #Create lookup table

               #find the value of every percentile from 0-100 ignoring NA values
               temp_lookup[col]= np.nanpercentile(state_data[col], pct_list) 

          #append mean values to end of lookup table
          temp_lookup = pd.concat([temp_lookup, means], axis = 0)     
          
          #set REGION cell in mean row to the state name. This is done twice, but doing so this way preserves row order.
          temp_lookup['REGION'] = state  
          
          #append state lookup table to the combined lookup table.
          lookup = pd.concat([lookup, temp_lookup]) 
          

     print("Lookup Table Complete")

     for state in pd.unique(ejscreen_data_df['ST_ABBREV']):

          print(state)

          #get state lookup table for state being operated on
          state_lookup = lookup[lookup['REGION'] == state] 

          #isolate state data from source dataset
          state_data = ejscreen_data_df[ejscreen_data_df['ST_ABBREV'] == state] 

          for col in percentile_column_names:
               
               #isolate column in lookup table
               lookupList = (state_lookup[col].values.tolist())  

               #Calculate EJScreen Percentiles
               ejscreen_data_df.update(state_data[col].apply(lambda x: getPctile(lookupList, x))) #calculate percentiles for input data

     print('Renaming Columns...')
     for col in percentile_column_names:
        
        #rename columns in ejscreen percentiles dataset
        ejscreen_data_df.rename(columns = {col: ("P_" + col)}, inplace = True)

        #append ejscreen percentiles dataset to original dataset
        final_df[("P_" + col)] = ejscreen_data_df[("P_" + col)]

     #update field name that doesnt follow naming convention
     if "P_PRE1960PCT" in final_df.columns:   
        final_df.rename(columns={"P_PRE1960PCT":"P_LDPNT"}, inplace = True)
     
     #if true, output to excel and csv respectively
     if(output == True): 
          final_df.to_csv(output_csv_percentiles)
          lookup.to_excel(output_xlsx_lookup)
    
     return(final_df, lookup)

#-------------------------------------------------------------------------------
# Name:        calBinTxt
# Purpose:     Add Bin and Text fields to dataset based on "P_" percentile fields.
# 
# Parameters:
#   df - Required. Input data frame containing percentile columns starting with P_.
#   out_table - Optional. path to output csv that will contain output dataset.
#   output - Required. If False, csv output will not be written.
# 
# Returns:
#   Original data frame with Bin "B_" and Text "T_" fields appended. 
#-------------------------------------------------------------------------------

def calBinTxt(df, out_table = "", output = False): 
    
     print("Initializing...")

     p_col = [col for col in df if col.startswith("P_")]
     
     print("Getting percentile columns...")
     print(p_col)
     

     print("Working on Bin fields...")

     bindf = pd.DataFrame()
     for col in p_col:
          
          
          #Calculate EJScreen Percentiles
          df[(col.replace("P_", "B_"))] = df[col].apply(lambda x: getBin(x))
          
     print("Working on Text fields...")
     for col in p_col:
         
         df[(col.replace("P_", "T_"))] = (df[col].astype('Int64').astype("str") + " %ile")
     
         #df[(col.replace("P_", "T_"))] = (df[col].astype('Int64').astype("str").fillna("delete")+ " %ile")
         df[(col.replace("P_", "T_"))] = df[(col.replace("P_", "T_"))].replace("<NA> %ile", None)
     
        
     if(output == True):
         print("Writing to csv...")
         df.to_csv(out_table)
     
     print("Complete")
    
     return(df)

def getBin(pct):

     if pd.isna(pct):
        return None
     else:
        if pct >= 95:
            return 11
        elif pct >= 90 and pct < 95:
            return 10
        elif pct >= 80 and pct < 90:
             return 9
        elif pct >= 70 and pct < 80:
             return 8
        elif pct >= 60 and pct < 70:
            return 7
        elif pct >= 50 and pct < 60:
            return 6
        elif pct >= 40 and pct < 50:
            return 5
        elif pct >= 30 and pct < 40:
            return 4
        elif pct >= 20 and pct < 30:
            return 3
        elif pct >= 10 and pct < 20:
            return 2
        else:
            return 1


#-------------------------------------------------------------------------------
# Name:        exportSpatial
# Purpose:     Joins data frame to geometry and writes to geodatabase
# 
# Parameters:
#   areas - Path to feature class containing geometry being joined to data frame
#   data_df - Data frame to be joined to the geometry
#   output_fc - Path to output feature class in geodatabase
#   schema = path to csv file containing field update schema. Format can be found here: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/batch-update-fields.htm
#   join_field = the name of the ID field that will be used to join the dataframe to the spatial dataset
# 
#-------------------------------------------------------------------------------

def exportSpatial(areas, data_df, output_fc, schema = "", join_field = "ID"):

    import arcpy
    from arcgis import GeoAccessor, GeoSeriesAccessor

    
    print("Reading Spatial Dataset...")

    #convert block group feature class to spatial dataframe
    sdf = pd.DataFrame.spatial.from_featureclass(areas) 

    print("Merging Datasets...")

    #join ejscreen data to spatial dataframe based on ID
    ejscreen_df = pd.merge(sdf, data_df, on=join_field) 

    
    #set path of initial output featureclass to be the same as the source
    temp_path = os.path.dirname(areas) + "\output"  

    print("Writing to geodatabase...")
    
    #export joined spatial dataframe to feature class.
    temp = ejscreen_df.spatial.to_featureclass(location=temp_path, sanitize_columns = False) 

    if(schema != ""):
        print("Using schema to update fields...")

        #this allows you to set field order, aliases, data types, and string lenghts. 
        arcpy.management.BatchUpdateFields(temp, output_fc, schema) 

#-------------------------------------------------------------------------------
# Name:        getPctile
# Purpose:     Internal function used for calulating percentiles for each row of a lookup table
# 
#-------------------------------------------------------------------------------

def getPctile(lookup_list, data_value):
     
     if (math.isnan(data_value)):
          return(float('nan'))   
     else:
          #retrieves the index of the first value in the lookup table 
          #that is greater than or equal to the input value
          lookup_index = next(x for x, val in enumerate(lookup_list) 
                                  if val >= data_value)              
           
          if (lookup_index > 0):
                
                #Fall back one percentile (unless the input value is equal to the lookup table value)
                if(lookup_list[lookup_index] != data_value):         
                    lookup_index = lookup_index - 1
          
          
          #.index() returns the the index of the first appearance of an input value.   
          #this ensures that in the case of tied values, the lowest percentile is taken
          pctile = lookup_list.index(lookup_list[lookup_index])     
          
          return(pctile)

#-------------------------------------------------------------------------------
# Name:        calIndexes
# Purpose:     Internal function used for calulating 2 factor and 5 factor index raw values.
# 
#-------------------------------------------------------------------------------

def calIndexes(ejdf):
    
    for colname in col_names.index_names:
        if (colname[0:3] == "D2_"):
            ejdf[colname] = ejdf["P_" + colname[3:]] * ejdf["DEMOGIDX_2"]
        if (colname[0:3] == "D5_"):
            ejdf[colname] = ejdf["P_" + colname[3:]] * ejdf["DEMOGIDX_5"]
    
    return(ejdf)