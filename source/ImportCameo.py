#The goal of this tool is to create File GDB and FCs from Cameo export *.zip
import sys, os, arcpy, zipfile, glob, numpy, re, shutil, csv
from tempfile import NamedTemporaryFile

def extractZip(pathToZip):
    #Extract to same folder that contains the zip
    # could put this in a folder with the same name as the zip??
    folderPath = os.path.dirname(pathToZip)

    zipFile = zipfile.ZipFile(pathToZip, 'r')
    for files in zipFile.namelist():
        zipFile.extract(files, folderPath)
    zipFile.close() 

    return folderPath

def createOutputGDB(parentFolder, gdbName):
    
    gdbPath = parentFolder + os.sep + gdbName + ".gdb"

    arcpy.env.workspace = gdbPath

    if not arcpy.Exists(gdbPath):
        gdbPath = arcpy.CreateFileGDB_management(parentFolder, gdbName)

    return str(gdbPath)

def tablesToGDB(folderPath, outGDBPath, nameOfSpatialTable, xFieldName, yFieldName):    
    #find all *.mer files
    newFileExt = ".csv"
    oldFileExt = ".mer"
    files = glob.glob(folderPath + os.sep + "*" + oldFileExt)

    for file in files:
        currentFileName = os.path.basename(file)
        currentFile = "{0}\\{1}".format(folderPath,currentFileName)

        newFileName = currentFileName.replace(oldFileExt, newFileExt)
        newFile = "{0}\\{1}".format(folderPath,newFileName)
        
        #TODO...look at why they were doing ASCII stuff
        #rename *.mer to *.csv
        shutil.move(currentFile, newFile)
        #os.rename(currentFile, newFile) #could fail if current files exist

        if newFileName.replace(newFileExt,'') == nameOfSpatialTable: 
            #TODO need to understand how to know what table has spatial details
            # and what to do with
            r = createSpatialData(newFile, xFieldName, yFieldName, outGDBPath)
        else:
            #table to table removing .csv ext
            r = arcpy.TableToTable_conversion(newFile, 
                                              outGDBPath, 
                                              newFileName.replace(newFileExt,""))

        #cleanup old file
        os.remove(newFile)

        print(file)
        print(str(r))

def createRelationshipClass(parentTable, primaryKey, childTable, foreignKey):
    #in case full path is provided TODO...check if this is necessary
    parentTableName = os.path.basename(parentTable)

    #in case full path is provided TODO...check if this is necessary
    childTableName = os.path.basename(childTable)

    #TODO...check both parent and child to ensure no spaces or other rules are broken
    arcpy.CreateRelationshipClass_management(arcpy.env.workspace + os.sep + parentTable, 
                                             arcpy.env.workspace + os.sep + childTable, 
                                             "{0}_{1}".format(parentTableName, childTableName),
                                             "SIMPLE",
                                             "Owns",
                                             "Is Owned By",
                                             "FORWARD",
                                             "ONE_TO_MANY",
                                             "NONE",
                                             primaryKey,
                                             foreignKey)

def createRelationshipClasses(relationships):
    for mainTable in relationships.keys():
        parentTable = ""
        parentTableFieldName = ""
        for tableMap in relationships[mainTable]:
            #this expects the data structure to contain: 
            #{ <ParentTableName> : [{ <ParentTableName> : <ParentKeyFieldName> }, {<ChildTableName> : <ChildFieldName>}, {<ChildTableName(n)> : <ChildFieldName(n)>}]
            # so just keep re-using the parent table/field name against all child table/field name(s)
            if tableMap.keys()[0] != mainTable:
                childTableName = tableMap.keys()[0]
                childTableFieldName = tableMap[childTableName]
                createRelationshipClass(parentTable, 
                                        parentTableFieldName, 
                                        childTableName, 
                                        childTableFieldName)
            else:
                parentTable = tableMap.keys()[0]
                parentTableFieldName = tableMap[parentTable]

def createSpatialData(table, fieldLat, fieldLon, outGDB):
    sr = arcpy.SpatialReference(4326)
    
    tempfile = NamedTemporaryFile(delete=False)

    #update table to use 0,0 for points with no lat lon
    with open(table, 'rb') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter=',', quotechar='"')
        writer = csv.writer(tempfile, delimiter=',', quotechar='"')
        
        latIndex = -1
        lonIndex = -1
        for row in reader:
            #print(row)
            #will only update the rows if the fields are found
            if latIndex < 0 and lonIndex < 0:
                index = 0
                for value in row:
                    if str(value) == fieldLat:
                        latIndex = index
                    if str(value) == fieldLon:
                        lonIndex = index
                    index += 1
            else:
                #if the row has empty value for either Lat or Lon then set as 0,0
                if row[latIndex] == "" or row[lonIndex] == "":
                    row[latIndex], row[lonIndex] = 0, 0

            writer.writerow(row)

    shutil.move(tempfile.name, table)

    tableName = os.path.splitext(os.path.basename(table))[0]
    tempLayerName = tableName + "_tempLayer"

    xyEventLayer = arcpy.MakeXYEventLayer_management(table, fieldLat, fieldLon, tempLayerName, sr)
    outFC = outGDB + os.sep + tableName
    outData = arcpy.CopyFeatures_management(xyEventLayer, outFC)

    return outData

def addAtachments(searchFolder, table, parentJoinField):
    idFieldName = "fieldID"
    valueFieldName = "fieldValue"

    #first enable attachments
    arcpy.EnableAttachments_management(arcpy.env.workspace + os.sep + table)

    #create attachemnt table (<FieldValueToJoinOn>, <pathToResource>)
    attachmentTable = createAttachmentTable(searchFolder, idFieldName, valueFieldName)

    # could look at using the working directory arg here to support longer paths to the attachments
    arcpy.AddAttachments_management(arcpy.env.workspace + os.sep + table, 
                                    parentJoinField, 
                                    attachmentTable, 
                                    idFieldName, 
                                    valueFieldName)

def createAttachmentTable(parentFolder, idFieldName, valueFieldName):
    #The GP tool create attachment table does not seem to support
    # the folder structure we are dealing with. So handeling here

    fields = (idFieldName, valueFieldName)

    #Table (JoinFieldIDValue, path to resource)
    tmp_table = os.path.join('in_memory', 'table_template')
    arcpy.CreateTable_management(*os.path.split(tmp_table))
    
    # TODO...could paths be longer than 250...should look at relative path options
    for field in fields:
        arcpy.AddField_management(tmp_table, field, "TEXT", field_length=250)

    cur = arcpy.da.InsertCursor(tmp_table, fields)

    for subdir, dirs, files in os.walk(parentFolder):
        for file in files:
            cur.insertRow((os.path.basename(subdir), os.path.join(subdir, file)))

    del cur
 
    return tmp_table

if __name__ == "__main__":
    
    arcpy.env.overwriteOutput = True

    ##Path to *.zip
    ##Example Usage: r"D:\Solutions\Cameo\test\LEPC3_all_HA_NCF_July2014.zip"
    zipPath = r"D:\Solutions\Cameo\test\LEPC3_all_HA_NCF_July2014.zip"

    ###Path to output workspace...could derive this from the zip
    ##Example Usage: r"D:\Solutions\Cameo\test"
    outWorkspacePath = r"D:\Solutions\Cameo\New folder"

    ##Name of output gdb...or I could just make this the name of the zip...after I handle invalid chars
    ##Example Usage: "testDataOutput"
    gdbName = "testDataOutput"

    #TODO work out how this is known
    nameOfSpatialTable = "Facilities"
    xFieldName = "Latitude"
    yFieldName = "Longitude"

    #what field contains the same values as used for naming the attachment folders in the zip
    attachmentIDFieldName = "FacilityRecordID"

    #data expected:
    #{ <ParentTableName> : [
        #{ <ParentTableName> : <ParentKeyFieldName> }, 
        #{<ChildTableName> : <ChildFieldName>}, 
        #{<ChildTableName(n)> : <ChildFieldName(n)>}
        #]}     
    
    #trying to understand if these would ever be different
    #I can determine most of these from the data if the ID values follow the specific rules
    #just want to work through this in the easiest way for the user while still allowing the 
    # the tool to be flexable enough to not fall over on some minor differences
    relationships = { 
        "Facilities" : [
            { "Facilities" : "FacilityRecordID" }, 
            { "FacilityIDs" : "FacilityRecordID" }, 
            { "Incidents" : "FacilityRouteRecordID" },
            { "ChemInvLocations" : "FacilityRouteRecordID" },
            { "ScreeningAndScenarios" : "FacilityRouteRecordID" },
            { "MapData" : "ParentRecordID" },
            { "SitePlanLink" : "FacilityRecordID" }
        ],
        "ChemInvLocations": [
            { "ChemInvLocations" : "ChemInInvRecordID" }, 
            { "ChemicalsInInventory" : "ChemInvRecordID" }, 
            { "ChemInvMixtures" : "ChemInvRecID" },
            { "ChemInvLocations" : "FacilityRouteRecordID" }
        ],
        "Routes": [
            { "Routes" : "RouteRecordID" }, 
            { "RouteIntersections" : "RouteRecordID" }
        ],
        "Contacts": [
            { "Contacts" : "ContactRecordID" }, 
            { "Phone" : "ParentRecordID" }
        ]}

    extractedFileLocation = extractZip(zipPath) 

    outGDBPath = createOutputGDB(outWorkspacePath, gdbName)

    tablesToGDB(extractedFileLocation, outGDBPath, nameOfSpatialTable, xFieldName, yFieldName)

    createRelationshipClasses(relationships)

    #not sure if we need to account for multiple attachment folders
    for dir in [d for d in os.listdir(extractedFileLocation) 
                if os.path.isdir(os.path.join(extractedFileLocation,d)) 
                and not d == os.path.basename(outGDBPath)]:
            addAtachments(extractedFileLocation + os.sep + dir, nameOfSpatialTable, attachmentIDFieldName)
