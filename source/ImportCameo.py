"""
-------------------------------------------------------------------------------
 | Copyright 2015 Esri
 |
 | Licensed under the Apache License, Version 2.0 (the "License");
 | you may not use this file except in compliance with the License.
 | You may obtain a copy of the License at
 |
 |    http://www.apache.org/licenses/LICENSE-2.0
 |
 | Unless required by applicable law or agreed to in writing, software
 | distributed under the License is distributed on an "AS IS" BASIS,
 | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 | See the License for the specific language governing permissions and
 | limitations under the License.
 ------------------------------------------------------------------------------
 """
#The goal of this tool is to create File GDB and FCs from CAMEO export *.zip
import sys, os, arcpy, zipfile, glob, shutil, csv, datetime, re
from datetime import date

# Defines tables that will be converted to feature classes, x/y fields are specified for each
NAMES_OF_SPATIAL_TABLES = {
    "Facilities" : {
        "LatField": "Latitude",
        "LonField" : "Longitude"
    },
    "SpecialLocations" : {
        "LatField": "SpLatitude",
        "LonField" : "SpLongitude"
    },
    "Incidents" : {
        "LatField": "InLatitude",
        "LonField" : "InLongitude"
    },
    "Resources" : {
        "LatField": "ReLatitude",
        "LonField" : "ReLongitude"
    }
}

# Defines CAMEO Tables that can potentially have documents or images attached and the ID field that would be used to link to the attachment
TABLES_WITH_ATTACHMENTS = {
    "Facilities" : "FacilityRecordID",
    "SpecialLocations": "SpecialLocRecordID",
    "Incidents": "IncidentRecordID",
    "Resources": "ResourceRecordID",
    "Routes" : "RouteRecordID",
    "Contacts" : "ContactRecordID"
}

ATTACHMENT_DIR_NAME = "SitePlansTemp"
SPATIAL_REFERENCE = arcpy.SpatialReference(4326)

# THIS NEEDS TO BE UPDATED IF ADDITIONAL RELATIONSHIPS EXIST
#{ <ParentTableName> : [
    #{ <ParentTableName> : <ParentKeyFieldName> }, 
    #{<ChildTableName> : <ChildFieldName>}, 
    #{<ChildTableName(n)> : <ChildFieldName(n)>}
    #]}    
RELATIONSHIPS = { 
        "Facilities" : [
            { "Facilities" : "FacilityRecordID" }, 
            { "FacilityIDs" : "FacilityRecordID" }, 
            { "Incidents" : "FacilityRouteRecordID" },
            { "ChemInvLocations" : "FacilityRouteRecordID" },
            { "ScreeningAndScenarios" : "FacilityRouteRecordID" },
            { "ContactsLink" : "OtherRecordID"},
            { "Phone" : "ParentRecordID" },
            { "SitePlanLink" : "FacilityRecordID" },
            { "MapData" : "ParentRecordID" }
        ],
        "Incidents" : [
            { "Incidents" : "IncidentRecordID" }, 
            { "IncidentMaterials" : "IncidentRecordID" },
            { "ContactsLink" : "OtherRecordID"},
            { "SitePlanLink" : "FacilityRecordID" }
        ],
        "SpecialLocations" : [
            { "SpecialLocations" : "SpecialLocRecordID" }, 
            { "ContactsLink" : "OtherRecordID"},
            { "Phone" : "ParentRecordID" },
            { "SitePlanLink" : "FacilityRecordID" },
            { "MapData" : "ParentRecordID" }
        ],
        "Resources" : [
            { "Resources" : "ResourceRecordID"},
            { "ResourceEquipt" : "RecordKey"},
            { "ContactsLink" : "OtherRecordID"},
            { "Phone" : "ParentRecordID" },
            { "SitePlanLink" : "FacilityRecordID" },
            { "MapData" : "ParentRecordID" }  
        ],
        "Routes": [
            { "Routes" : "RouteRecordID" }, 
            { "RouteIntersections" : "RouteRecordID" },
            { "Incidents" : "FacilityRouteRecordID"},
            { "ChemInvLocations" : "FacilityRouteRecordID" },
            { "ScreeningAndScenarios" : "FacilityRouteRecordID" },
            { "SitePlanLink" : "FacilityRecordID" },
            { "MapData" : "ParentRecordID" },
        ],
        "ChemInvLocations": [
            { "ChemInvLocations" : "ChemInInvRecordID" }, 
            { "ChemicalsInInventory" : "ChemInvRecordID" }, 
            { "ChemInvMixtures" : "ChemInvRecID" }
        ],
        "Contacts": [
            { "Contacts" : "ContactRecordID" }, 
            { "Phone" : "ParentRecordID" },
            { "ContactsLink" : "ContactRecordID"},
            { "SitePlanLink" : "FacilityRecordID" }
        ]}

def extract_zip(path_to_zip):
    """Extracts the zip to its parent folder"""
    try:
        arcpy.AddMessage("Extracting zip...")
        folder_path = os.path.dirname(path_to_zip)
        sub_folder_path = ""
        zip_file = zipfile.ZipFile(path_to_zip, 'r')
        for file in zip_file.namelist():
            if sub_folder_path == "":
                sub_path =  file.split("/")
                if len(sub_path) > 0:
                    sub_folder_path += folder_path + os.sep + os.sep.join(sub_path[:-1])
            zip_file.extract(file, folder_path)
        zip_file.close()
        arcpy.AddMessage("  zip extracted")
        arcpy.AddMessage("-"*50)
        if sub_folder_path != "":
            return sub_folder_path
        else:
            return folder_path
    except Exception:
        arcpy.AddError("Error occurred while extracting zip file")
        raise

def create_output_gdb(parent_folder, gdb_name):
    """Creates a new gdb for the results"""
    arcpy.AddMessage("Checking output workspace...")
    gdb_path = parent_folder + os.sep + gdb_name + ".gdb"
    #generate a unique name if the gdb already exists
    if arcpy.Exists(gdb_path):
        arcpy.AddWarning("    " + gdb_path + " already exists...creating a unique name for the workspace")
        unique_name = arcpy.CreateUniqueName(gdb_name + ".gdb", parent_folder)
        gdb_path = unique_name
    arcpy.AddMessage("Creating GDB: " + gdb_path)
    arcpy.CreateFileGDB_management(os.path.dirname(gdb_path), os.path.basename(gdb_path))
    arcpy.env.workspace = str(gdb_path)
    arcpy.AddMessage("-"*50)
    return str(gdb_path)
   
def create_relationship_class(parent_table, primary_key, child_table, foreign_key):
    """creates the relationship class"""
    try:
        # get parent table and check if exists
        parent_table_name = os.path.basename(parent_table)
        full_parent_table_path = arcpy.env.workspace + os.sep + parent_table
        parent_exists = arcpy.Exists(full_parent_table_path)

        # get child table and check if exists
        child_table_name = os.path.basename(child_table)
        full_child_table_path = arcpy.env.workspace + os.sep + child_table
        child_exists = arcpy.Exists(full_child_table_path)
        
        #name for rel class
        out_relationship_class_name = "{0}_{1}".format(parent_table_name, child_table_name)

        #populated if the given table does not exist
        return_issues = []

        #verify that both tables exist prior to creating the relationship class
        if parent_exists and child_exists:
            arcpy.CreateRelationshipClass_management(full_parent_table_path, 
                                                     full_child_table_path, 
                                                     out_relationship_class_name,
                                                     "SIMPLE",
                                                     child_table_name,
                                                     "Parent",
                                                     "FORWARD",
                                                     "ONE_TO_MANY",
                                                     "NONE",
                                                     primary_key,
                                                     foreign_key)
            arcpy.AddMessage("  created: " + out_relationship_class_name)
        else:
            
            if not parent_exists:
                return_issues.append(full_parent_table_path)
            if not child_exists:
                return_issues.append(full_child_table_path)
        return return_issues
    except arcpy.ExecuteError:
        arcpy.AddError("Error creating relationship between {0} and {1}".format(parent_table, child_table))
        raise

def create_relationship_classes(relationships):
    """Loop through the RELATIONSHIPS dictionary and create the relationship classes"""
    arcpy.AddMessage("Creating relationship classes...")
    rel_issues = []
    for main_table in list(relationships.keys()):
        parent_table = ""
        parent_table_field_name = ""
        for table_map in relationships[main_table]:
            #this expects the data structure to contain: 
            #{ <ParentTableName> : [{ <ParentTableName> : <ParentKeyFieldName> }, {<ChildTableName> : <ChildFieldName>}, {<ChildTableName(n)> : <ChildFieldName(n)>}]
            # so just keep re-using the parent table/field name against all child table/field name(s)
            if list(table_map.keys())[0] != main_table:
                child_table_name = list(table_map.keys())[0]
                child_table_field_name = table_map[child_table_name]
                rel_issue = create_relationship_class(parent_table, 
                                        parent_table_field_name, 
                                        child_table_name, 
                                        child_table_field_name)
                if len(rel_issue) > 0:
                    for issue in rel_issue:
                        rel_issues.append(issue)
            else:
                parent_table = list(table_map.keys())[0]
                parent_table_field_name = table_map[parent_table]
    arcpy.AddMessage("Relationship classes created")
    #if len(rel_issues) > 0:
        #arcpy.AddWarning("Please review the RELATIONSHIPS variable in the source Python file to ensure it is valid")
        #arcpy.AddWarning("Relationship classes for the following tables were not created as the table(s) did not exist:")
        #for issue in rel_issues:
            #arcpy.AddWarning(issue)
    arcpy.AddMessage("-"*50)

def add_attachments(extracted_file_location, out_gdb_path):
    """Loop through attachment folders and add the attachments"""
    try:
        attachment_full_path = extracted_file_location + os.sep + ATTACHMENT_DIR_NAME
        available_tables = arcpy.ListFeatureClasses() + arcpy.ListTables()
        for table, idField in TABLES_WITH_ATTACHMENTS.items():
            #Check to see if table is in the geodatabase, not all CAMEO ZIPs will have ALL of the possible TABLE_WITH_ATTACHMENTS
            if table in available_tables:
                arcpy.AddMessage("Adding attachments to {}...".format(table))
                if os.path.exists(attachment_full_path):
                    add_attachment(attachment_full_path, table, idField)
                else:
                    arcpy.AddWarning("Expected attachment path does not exist: " + attachment_full_path)
                arcpy.AddMessage(" attachments added")
    except Exception:
        arcpy.AddError("Error occurred while adding attachments")  
        raise    

def remove_attachment_folder(extracted_file_location, out_gdb_path):

    attachment_full_path = extracted_file_location + os.sep + ATTACHMENT_DIR_NAME

    if os.path.exists(attachment_full_path):
        shutil.rmtree(attachment_full_path)
        arcpy.AddMessage("Removed attachment folder: {}\n".format(attachment_full_path))

def add_attachment(search_folder, inTable, att_id_field):
    """Enable and add the attachments """
    #fields added to support the attachment table generated
    id_field_name = "fieldID"
    value_field_name = "fieldValue"

    #first enable attachments
    arcpy.EnableAttachments_management(arcpy.env.workspace + os.sep + inTable)

    #create attachemnt table (<FieldValueToJoinOn>, <pathToResource>)
    attachment_table = create_attachment_table(search_folder, id_field_name, value_field_name)

    #TODO could look at using the working directory arg here to support longer paths to the attachments
    arcpy.AddAttachments_management(arcpy.env.workspace + os.sep + inTable, 
                                    att_id_field, 
                                    attachment_table, 
                                    id_field_name, 
                                    value_field_name)

def create_attachment_table(parent_folder, id_field_name, value_field_name):
    """The GP tool CreateAttachmentTable does not support the folder structure"""
    """ we are dealing with...handeling here"""
    fields = [id_field_name, value_field_name]

    #Table (JoinFieldIDValue, path to resource)
    tmp_table = os.path.join('in_memory', 'table_template')
    arcpy.CreateTable_management(*os.path.split(tmp_table))
    
    for field in fields:
        arcpy.AddField_management(tmp_table, field, "TEXT", field_length=500)

    cur = arcpy.da.InsertCursor(tmp_table, fields)

    for subdir, dirs, files in os.walk(parent_folder):
        for file in files:
            cur.insertRow((os.path.basename(subdir), os.path.join(subdir, file)))
    del cur
    return tmp_table
 
def check_date(value):
    """Test value to confirm if it's a supported date value"""
    date_formats = ["%m/%d/%y", "%m/%d/%Y"]
    is_date = False
    test_complete = False
    if value != "":
        test_complete = True
        if len(value.split("/")) == 3:
            for format in date_formats:
                try:
                    datetime.datetime.strptime(value, format)
                    is_date = True
                    break
                except:
                    is_date = False
    return is_date, test_complete

def check_float(value):
    """TypeCheck value to confirm if it's a valid float"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def reverse_numeric(x, y):
    return y - x

def remove_null(collection, null_fields):
    if len(null_fields) > 0:
        #sort the values so we can remove the highest index first and not affect the lower index values
        null_fields_sort = sorted(null_fields, cmp=reverse_numeric)
        for nf in null_fields_sort:
            del collection[nf]

def get_fields(reader):
    """Reads field values to determine appropriate field length"""
    fields = {}
    first_row = True
    #first read the records and build the list
    for row in reader:  
        index = 0   
        #{fieldIndex:(fieldName, size, type, testComplete)}
        if first_row:
            first_row = False
            for field_name in row:               
                fields[index] = [field_name, 1000, "Text", False] #default to "Text"
                index += 1
        else:
            error_row = True if len(row) != len(fields) else False
            for value in row:
                if error_row and index == len(fields):
                    break
                current_length = len(value)
                if fields[index][1] < current_length: 
                    if current_length in range(0, 249): 
                        fields[index][1] = 1500
                    elif current_length in range(250, 499):
                        fields[index][1] = 3000
                    elif current_length in range(500, 999):
                        fields[index][1] = 5000
                    else:
                        #if the value exceeds 1000 then round it UP to the nearest thousand
                        # and use that for the length
                        current_length -= current_length % -1000
                        fields[index][1] = current_length
                if not fields[index][3]:
                    is_date, test_complete = check_date(value)
                    if is_date:
                        fields[index][2] = "Date"
                    fields[index][3] = test_complete
                index += 1

    del row
    return fields

def tables_to_gdb(folder_path, out_gdb_path):    
    """Rename .mer to .csv and load the data"""
    try:
        #find all *.mer files
        new_file_ext = ".csv"
        old_file_ext = ".mer"
        latField = None
        lonField = None
        files = glob.glob(folder_path + os.sep + "*" + old_file_ext)

        for file in files:
            current_file_name = os.path.basename(file)
            current_file = "{0}\\{1}".format(folder_path, current_file_name)

            new_file_name = current_file_name.replace(old_file_ext, new_file_ext)
            new_file = "{0}\\{1}".format(folder_path, new_file_name)
        
            #rename *.mer to *.csv
            shutil.move(current_file, new_file)

            is_spatial = False
            baseName = new_file_name.replace(new_file_ext, '')
            if baseName in NAMES_OF_SPATIAL_TABLES: 
                is_spatial = True
                latField = NAMES_OF_SPATIAL_TABLES[baseName]['LatField']
                lonField = NAMES_OF_SPATIAL_TABLES[baseName]['LonField']
            t = create_and_populate_table(new_file, out_gdb_path, is_spatial, latField, lonField)
            #cleanup old file
            os.remove(new_file)
    except Exception:
        arcpy.AddError("Error occurred while loading the data")
        raise

def create_and_populate_table(table, out_gdb, is_spatial, lat_field=None, lon_field=None):
    """Create the output table and populate its values"""
    with open(table, 'rt') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='"')       
        fields = get_fields(reader)
        del(reader)

    table_name = os.path.basename(table).replace(".csv", "")
    table_name = arcpy.ValidateTableName(table_name, out_gdb)
    outTable = out_gdb + os.sep + table_name
    if arcpy.Exists(outTable):
        arcpy.AddMessage("Appending Additional Records to Table: " + str(table_name))
    else:
        arcpy.AddMessage( "Adding Table: " + str(table_name))

    if is_spatial:
        new_table = arcpy.CreateFeatureclass_management("in_memory", 
                                                table_name, 
                                                "Point", 
                                                spatial_reference = SPATIAL_REFERENCE)
    else:
        new_table = arcpy.CreateTable_management("in_memory", table_name)      
    arcpy.AddMessage("  Table Added: " + out_gdb + os.sep + table_name)
    arcpy.AddMessage("  Adding new fields...")
    index = 0
    null_fields = []
    #fieldsDescriptions = []
    for field in fields:
        f = fields[index]
        field_name = str(f[0])
        field_name = arcpy.ValidateFieldName(field_name, out_gdb)
        f[0] = field_name
        if field_name not in ["", " ", None]:
            arcpy.AddField_management(new_table,
                                        field_name,
                                        field_type = f[2],
                                        field_length= int(f[1]))
            #fieldsDescriptions.append([field_name, f[2], f[0], int(f[1])])
        else:
            arcpy.AddWarning("{0}: contains a field with a missing name at index {1}".format(table_name, str(index)))
            arcpy.AddWarning("No new field was added for index " + str(index))
            null_fields.append(index)
        index += 1

    #remove any fields with NULL name from fields collection
    remove_null(fields, null_fields)

    if is_spatial:
        add_data(table, new_table, lat_field, lon_field, fields, null_fields)
    else:
        add_data(table, new_table, None, None, fields, null_fields)

    #Check to see if table already already exists in output geodatabase
    #if table exists then append features from input ZIP file
    #This is to support processing multiple input ZIP files
    
    outTable = out_gdb + os.sep + table_name
    if arcpy.Exists(outTable):
        existingTableFields = sorted([field.name for field in arcpy.ListFields(outTable)])
        newTableFields = sorted([field.name for field in arcpy.ListFields(new_table)])
        #Check to see if any additional fields need to be added to the source table
        if existingTableFields != newTableFields:
            fieldListToAdd = [fieldname for fieldname in newTableFields if fieldname not in existingTableFields]
            fieldsToAdd = [field for field in arcpy.ListFields(new_table) if field.name in fieldListToAdd and field.type != "OID"]
            for field in fieldsToAdd:
                arcpy.AddField_management(outTable,field.name,field.type, field_length=field.length)
        arcpy.Append_management(new_table,outTable,schema_type="NO_TEST")
    else:
        if is_spatial:
            arcpy.CopyFeatures_management(new_table, outTable)
        else:
            arcpy.CopyRows_management(new_table, outTable)
    
    arcpy.Delete_management("in_memory")

def add_data(table, new_table, field_lat=None, field_lon=None, fields=None, null_fields=None):
    """Reads data from csv and writes to the new gdb table""" 
    """Handles tables or tables with shape if lat and lon fields are provided"""
    field_name_list = list(list(zip(*list(fields.values())))[0])
    is_spatial = False
    if field_lat != None and field_lon != None:
        is_spatial = True
        field_name_list.append("SHAPE@")
    lat_index = -1
    lon_index = -1
    arcpy.AddMessage("  Importing data...")
    row_index = 0
    with open(table, 'rt') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='"')  
        with arcpy.da.InsertCursor(new_table, field_name_list) as cursor:  
            first_row = True
            for row in reader:
                row_index += 1 
                if len(null_fields) > 0:
                    remove_null(row, null_fields)
                has_xy = False
                new_row = None
                #first row has column headers
                if first_row:
                    first_row = False
                    #if this is the spatial data then get the index for the
                    # lat and lon fields so we can use these in the geom we create
                    if is_spatial:
                        if lat_index < 0 and lon_index < 0:
                            index = 0
                            for value in row:
                                if str(value) == field_lat:
                                    lat_index = index
                                if str(value) == field_lon:
                                    lon_index = index
                                index += 1
                else:
                    xx = 0
                    error_row = True if len(row) != len(fields) else False
                    for value in row:
                        if error_row and xx == len(fields):
                            arcpy.AddWarning("Row: {0} in {1} contains more values than fields".format(str(row_index), csv_file)) 
                            arcpy.AddWarning(row)
                            while xx < len(row):
                                del row[-1]
                            break
                        #remove non ascii if any
                        new_value = ''.join([i if ord(i) < 128 else '' for i in str(value)])
                        #if this changes the string then update the row
                        if new_value != value:
                            if new_row != None:
                                new_row[xx] = new_value
                            else:
                                row[xx] = new_value
                        if fields[xx][2] == "Date":
                            #check for valid date value
                            if not check_date(new_value)[0]:
                                #set default if valid date not found
                                if new_row != None:
                                    new_row[xx] = None
                                else:
                                    row[xx] = None
                        if is_spatial and not has_xy:
                            #row is from our reader...create a new row to append the new shape
                            if row[lat_index] in ["", None] or row[lon_index] in ["", None] or not check_float(row[lon_index]) or not check_float(row[lat_index]):
                                row[lat_index], row[lon_index] = 0, 0
                            new_row = list(row)
                            new_row.append([float(row[lon_index]), float(row[lat_index])])
                            has_xy = True
                        xx+=1
                    if new_row:
                        cursor.insertRow(new_row)
                    else:
                        cursor.insertRow(row)
        arcpy.AddMessage("-"*50)

def main():
    arcpy.env.overwriteOutput = True

    #Check for basic license
    # Basic doesn't support the GP tools for adding relationships or attachments
    product_info = str(arcpy.ProductInfo())
    if product_info == 'ArcView':
        arcpy.AddWarning("Basic license level does not support the adding of relationship classes or attachments.")
        arcpy.AddWarning("Tables will be generated without relationship classes or attachments")

    ##Path to *.zip
    ##Example Usage: r"C:\DATA_all_July2014.zip"
    zip_paths = [valueObject.value for valueObject in arcpy.GetParameter(0)]

    ###Path to output workspace...could derive this from the zip
    ##Example Usage: r"C:\temp"
    out_workspace_path = arcpy.GetParameterAsText(1)

    ##Name of output gdb
    ##Example Usage: "testDataOutput"
    gdb_name = arcpy.GetParameterAsText(2)
  
    #create the output workspace
    out_gdb_path = create_output_gdb(out_workspace_path, gdb_name)

    #import the data into gdb tables
    for zip_path in zip_paths:
        #extract the zip file
        extracted_file_location = extract_zip(zip_path)
        #convert to .mer files to GDB tables
        tables_to_gdb(extracted_file_location, out_gdb_path)
        if product_info != 'ArcView':
            #add the attachments
            add_attachments(extracted_file_location, out_gdb_path)
            #remove attachmnet folder from directory after attachment to GDB
            remove_attachment_folder(extracted_file_location, out_gdb_path)

    if product_info != 'ArcView':
        #create appropriate relationship classes
        create_relationship_classes(RELATIONSHIPS)

    #Set Derived Parameter Values
    # derived values are added to the map

    arcpy.env.workspace = out_gdb_path

    out_tables = arcpy.ListTables()

    out_tables = ";".join([out_gdb_path + os.sep + table for table in out_tables if "__ATTACH" not in table])

    out_FCs = arcpy.ListFeatureClasses()

    out_FCs = ";".join(sorted([out_gdb_path + os.sep + fc for fc in out_FCs if "__ATTACH" not in fc], reverse=True))

    arcpy.SetParameterAsText(3, out_FCs)

    arcpy.SetParameterAsText(4, out_tables)

if __name__ == "__main__":
    main()

