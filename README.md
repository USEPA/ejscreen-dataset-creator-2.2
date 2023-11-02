# EJScreenDatasetCreator

## Description
`EJScreenDatasetCreator` is a python tool that automates the calculation of EJScreen indexes(`calIndexes()`), percentiles(`percentileCal()`/`percentileCalState()`), bin/text fields(`calBinTxt()`), and lookup tables to create the production EJScreen 2023 dataset. You also have the option join the resultant table to matching block groups or tracts to create a feature class within an ESRI File Geodatabase(`exportSpatial`).

## Python Package Requirements
All required packages come preinstalled in the default ArcGIS Pro 3.1 environment, which includes python 3. The following are the packages and versions used in the development of this tool. 

| Package       | Version       | 
| ------------- |--------------:|
| python        | 3.9.16        | 
| pandas        | 1.4.4         | 
| numpy         | 1.20.1        | 
| arcgis        | 2.1.0.2       |  
| arcpy         | 3.1           |

ArcGIS Pro is required to export the results to an Esri feature class. 
## Input Requirements

A csv file  containing the required columns to generate an EJScreen dataset. These column names are designated in `col_names.py`. By default, you will need the following columns in your input:

| `col_names.info_names`       | `col_names.data_names`      | `col_names.extra_cols`      |
| ------------- | ------------- | ------------- |
| ID |  DEMOGIDX_2 | AREALAND | 
| STATE_NAME | DEMOGIDX_5 | AREAWATER | 
| ST_ABBREV | PEOPCOLORPCT | NPL_CNT | 
| CNTY_NAME | LOWINCPCT | TSDF_CNT | 
| REGION | UNEMPPCT | EXCEED_COUNT_80 | 
| ACSTOTPOP | LINGISOPCT | EXCEED_COUNT_80_SUP | 
| ACSIPOVBAS | LESSHSPCT | |
| ACSEDUCBAS | UNDER5PCT | |
| ACSTOTHH | OVER64PCT | |
| ACSTOTHU | LIFEEXPPCT | |
| ACSUNEMPBAS | PM25 | |
| PEOPCOLOR | OZONE | |
| LOWINCOME | DSLPM | |
| UNEMPLOYED | CANCER | |
| LINGISO | RESP | |
| LESSHS | RSEI_AIR | |
| UNDER5 | PTRAF | |
| OVER64 | PRE1960PCT | |
| PRE1960 | PNPL |  |
|  | PRMP | |
|  | PTSDF | |
|  | UST | |
|  | PWDIS | |

## How to Use

To run the tool, download the files to a local folder. From there, open `ejscreen_dataset.py` and update the following parameters:

*list parameters here

## EPA Disclaimer
The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use.  EPA has relinquished control of the information and no longer has responsibility to protect the integrity , confidentiality, or availability of the information.  Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA.  The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government. 


