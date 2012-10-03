'''BatchRasterExtractor.py

Author:
  Kelsey Kaszas
  Dept of Geography and Environmental Studies
  University of California, Los Angeles, USA
  kelsey.kaszas@gmail.com
  Special Thanks to Jida Wang 

Date created April 9 2012
Modified     July 27 2012

Purpose:
  Converts each shape in a feature class into a separate shapefile.
  Uses individual shapefiles to extract raster data by mask.
  Appends extracted raster files with "Value", "Area", and "Percent" fields. 
  Final output is a folder with masked raster subsets. 

Code Requirements:
  This code requires the user to have Python 2.6 for ArcGIS 10 (or above) installed on computer
  This code uses a custom python script called "Split Layer By Attributes" that can be downloaded from: http://arcscripts.esri.com/details.asp?dbid=14127
  This code requires ArcGIS Spatial Analyst Extension
  
Code Usage Guide [ IMPORTANT ] :
  1. change the ten places in code that have a comment on the right hand side (indicated by ' ### ') 
  2. save code [ CTRL + S ]
  3. run code [ F5 ]
  
Troubleshooting:
  1. If code returns a 'NoneType' error, close all files and re-run code
     (this error is due to the code's use of the custom tool "SplitLayerByAttributes")
  2. If code crashes while running, it is possible that polygons exist in the vector file that do not
     have corresponding raster data to extract. To fix this, manually remove those polygons using ArcMap
     
   
'''
#--------------------------------------------------------------------

#import system module 
import arcpy, os
from arcpy import env
from arcpy.sa import * 

#enable overwrite 
arcpy.env.overwriteOutput = True

#define filepath
filepath = r"D:\My Documents\RASTER_EXTRACTER"                                      ### change path to workspace folder
arcpy.ImportToolbox(r"D:\My Documents\SplitLayerByAttributes.tbx")                  ### change path to location of "Split Layer By Attributes" toolbox .tbx
symbologyLayer = r"D:\My Documents\GlobCover_Legend.lyr"                            ### comment out or delete this line if there is NO symbology .lyr file 


#set parameters 
#vector = arcpy.GetParameterAsText(0)
vector = r"D:\My Documents\vector.shp"                                              ### change path to vector dataset 


#raster = arcpy.GetParameterAsText(1)
raster = r"D:\My Documents\raster.tif"                                              ### change path to raster dataset

#out_vector = arcpy.GetParameterAsText(2)
out_vector = r"D:\My Documents\vector_output"                                       ### change path and change \vector_output to name of folder that will contain individual shapefiles
out_vector = str(out_vector)
os.makedirs(out_vector)

#out_raster = arcpy.GetParameterAsText(3)
out_raster = r"D:\My Documents\raster_output"                                       ### change path and change \raster_output to name of folder that will contain subset raster files                                                                                 
out_raster = str(out_raster)
os.makedirs(out_raster)

#set workspace environment 
arcpy.env.workspace = out_vector

#input pixel size of raster
z = ???                                                                             ### change ??? to pixel size of raster (units in meters) (example: z = 300)                                                           

#[SPLIT]
#_________________________________________________________________________

print("running split...")

#print(out_vector)

name_vector = '???'                                                                 ### choose naming convention: change ??? to the field name from original shapefile that output vector naming convention will be based on
arcpy.SplitLayerByAttributes(vector, name,"_",out_vector)                                                                          
print("split completed")

#[MASK]
#________________________________________________________________________

print("adding symbology layer to original raster file")
arcpy.ApplySymbologyFromLayer_management (raster, symbologyLayer)                   ### Comment out or delete this line of code if there is NO symbology .lyr file


#Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")


print("running mask of shapefile output")
for file1 in os.listdir(out_vector):    
    if file1.endswith(".shp"):
        
        #cursor out name of individual vector outputs for raster file naming convention 
        name = arcpy.SearchCursor(file1)
        for name_1 in name:
            raster_name = name_1.name_vector
            break       

        # Execute ExtractByMask
        outExtractByMask = ExtractByMask (raster, file1)  

        # Save the output
        outExtractByMask.save(out_raster + "/" + str(raster_name))



        print("performing statistics on raster. step 1...get a total pixel count from new raster subset")
        count_list = []
        value_list = []
        searched_rows = arcpy.SearchCursor(outExtractByMask)
        total_count = 0
        for row in searched_rows:
            value_list.append(row.VALUE)
            count_list.append(row.COUNT)
            total_count += row.COUNT

        print(str(total_count))

        
        print("step 2...creating tmp.dbf to serve as intermediary")
        tmpTABLE = "tmp.dbf"
        if os.path.exists(tmpTABLE):                                          
            os.remove(tmpTABLE)                                               
        
        arcpy.CreateTable_management(out_vector, tmpTABLE)

        print("step 3... add fields to tmp")
        #ADD FIELDS to tmp table
        arcpy.AddField_management(tmpTABLE, "VALUE", "LONG")
        arcpy.AddField_management(tmpTABLE, "area", "DOUBLE")
        arcpy.AddField_management(tmpTABLE, "percent", "DOUBLE") 
        print("table created")
        
        #UPDATE the tmp table with calculation in added fields
        new_row = arcpy.InsertCursor(tmpTABLE)
        searched_rows = arcpy.SearchCursor(outExtractByMask)
        index = 0
        print("step 4...update the tmp table with calculation in added fields")
        for searched_row in searched_rows:
    
            #print index
            row = new_row.newRow()
            row.VALUE = value_list[index]
            row.area = z*z*1.0*count_list[index]/1000000                                                                                  
            row.percent = count_list[index]*100.0/total_count
            index = index+1
            new_row.insertRow(row)
    
        del row
        del new_row
        del searched_row
        del searched_rows

        print("step 5 ...join the tmp table to attribute table of the newly subset raster file")         

        #join tables to the attribute table of the raster file
        arcpy.MakeRasterLayer_management (outExtractByMask,  "layerName")     
    
        # Join the feature layer to a table
        arcpy.JoinField_management("layerName", "VALUE", tmpTABLE, "VALUE")       
             
        if os.path.exists(tmpTABLE):                                          
            os.remove(tmpTABLE)


print("extract by mask completed")
