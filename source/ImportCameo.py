#The goal of this tool is to create File GDB and FCs from CAMEO export *.zip
import sys, os, arcpy, zipfile, glob, shutil, csv, datetime, re
from datetime import date

NAME_OF_SPATIAL_TABLE = "Facilities"
LAT_FIELD_NAME = "Latitude"
LON_FIELD_NAME = "Longitude"
ATTACHMENT_ID_FIELD = "FacilityRecordID"
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
                                                     "Is Owned By",
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
    if len(rel_issues) > 0:
        arcpy.AddWarning("Please review the RELATIONSHIPS variable in the source Python file to ensure it is valid")
        arcpy.AddWarning("Relationship classes for the following tables were not created as the table(s) did not exist:")
        for issue in rel_issues:
            arcpy.AddWarning(issue)
    arcpy.AddMessage("-"*50)

def add_attachments(extracted_file_location, out_gdb_path):
    """Loop through attachment folders and add the attachments"""
    try:
        arcpy.AddMessage("Adding attachments...")
        for dir in [d for d in os.listdir(extracted_file_location) 
                    if os.path.isdir(os.path.join(extracted_file_location, d)) 
                    and not d == os.path.basename(out_gdb_path)]:
                add_attachment(extracted_file_location + os.sep + dir)
        arcpy.AddMessage(" attachments added")
    except Exception:
        arcpy.AddError("Error occurred while adding attachments")  
        raise    

def add_attachment(search_folder):
    """Enable and add the attachments """
    #fields added to support the attachment table generated
    id_field_name = "fieldID"
    value_field_name = "fieldValue"

    #first enable attachments
    arcpy.EnableAttachments_management(arcpy.env.workspace + os.sep + NAME_OF_SPATIAL_TABLE)

    #create attachemnt table (<FieldValueToJoinOn>, <pathToResource>)
    attachment_table = create_attachment_table(search_folder, id_field_name, value_field_name)

    #TODO could look at using the working directory arg here to support longer paths to the attachments
    arcpy.AddAttachments_management(arcpy.env.workspace + os.sep + NAME_OF_SPATIAL_TABLE, 
                                    ATTACHMENT_ID_FIELD, 
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
                fields[index] = [field_name, 255, "Text", False] #default to "Text"
                index += 1
        else:
            for value in row:
                current_length = len(value)
                if fields[index][1] < current_length: 
                    if current_length in range(0, 249): 
                        fields[index][1] = 250
                    elif current_length in range(250, 499):
                        fields[index][1] = 500
                    elif current_length in range(500, 999):
                        fields[index][1] = 1000
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
        files = glob.glob(folder_path + os.sep + "*" + old_file_ext)

        for file in files:
            current_file_name = os.path.basename(file)
            current_file = "{0}\\{1}".format(folder_path, current_file_name)

            new_file_name = current_file_name.replace(old_file_ext, new_file_ext)
            new_file = "{0}\\{1}".format(folder_path, new_file_name)
        
            #rename *.mer to *.csv
            shutil.move(current_file, new_file)

            is_spatial = False
            if new_file_name.replace(new_file_ext, '') == NAME_OF_SPATIAL_TABLE: 
                is_spatial = True
            t = create_and_populate_table(new_file, out_gdb_path, is_spatial)
            #cleanup old file
            os.remove(new_file)
    except Exception:
        arcpy.AddError("Error occurred while loading the data")
        raise

def create_and_populate_table(table, out_gdb, is_spatial):
    """Create the output table and populate its values"""
    with open(table, 'rt') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='"')       
        fields = get_fields(reader)
        del(reader)

    table_name = os.path.basename(table).replace(".csv", "")
    table_name = arcpy.ValidateTableName(table_name, out_gdb)
    arcpy.AddMessage("Adding Table: " + str(table_name))

    if is_spatial:
        new_table = arcpy.CreateFeatureclass_management(out_gdb, 
                                                table_name, 
                                                "Point", 
                                                spatial_reference = SPATIAL_REFERENCE)
    else:
        new_table = arcpy.CreateTable_management(out_gdb, table_name)      
    arcpy.AddMessage("  Table Added: " + str(new_table))
    arcpy.AddMessage("  Adding new fields...")
    index = 0
    for field in fields:
        f = fields[index]
        field_name = str(f[0])
        field_name = arcpy.ValidateFieldName(field_name, out_gdb)
        f[0] = field_name
        arcpy.AddField_management(new_table,
                                    field_name,
                                    field_type = f[2],
                                    field_length= int(f[1]))
        index += 1
    if is_spatial:
        add_data(table, new_table, LAT_FIELD_NAME, LON_FIELD_NAME, fields)
    else:
        add_data(table, new_table, None, None, fields)

def add_data(table, new_table, field_lat=None, field_lon=None, fields=None):
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
    with open(table, 'rt') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='"')  
        with arcpy.da.InsertCursor(new_table, field_name_list) as cursor:  
            first_row = True
            for row in reader: 
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
                    for value in row:
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
    zip_path = arcpy.GetParameterAsText(0)

    ###Path to output workspace...could derive this from the zip
    ##Example Usage: r"C:\temp"
    out_workspace_path = arcpy.GetParameterAsText(1)

    ##Name of output gdb
    ##Example Usage: "testDataOutput"
    gdb_name = arcpy.GetParameterAsText(2)

    #extract the zip file
    extracted_file_location = extract_zip(zip_path) 
  
    #create the output workspace
    out_gdb_path = create_output_gdb(out_workspace_path, gdb_name)

    #import the data into gdb tables
    tables_to_gdb(extracted_file_location, out_gdb_path)

    if product_info != 'ArcView':
        #create appropriate relationship classes
        create_relationship_classes(RELATIONSHIPS)

        #add the attachments
        add_attachments(extracted_file_location, out_gdb_path)

if __name__ == "__main__":
    main()

