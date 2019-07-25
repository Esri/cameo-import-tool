import os
import arcpy
import collections

testDir = os.path.dirname(os.path.abspath(__file__))

toolBoxPath = os.path.abspath(os.path.join(testDir, "..", "source", "CAMEO Tools.tbx"))

mockCAMEOzip = os.path.abspath(os.path.join(testDir, "data", "MockCAMEOSampleData.zip"))
sampleCAMEOzip = os.path.abspath(os.path.join(testDir, "data", "SolutionCAMEOSampleData.zip"))

mockCAMEO_expResults = {
    "GDBPath" : os.path.join(testDir, "MockCAMEO.gdb"),
    "RelationshipClasses" : [
        'Facilities__ATTACHREL',
        'SpecialLocations__ATTACHREL',
        'Incidents__ATTACHREL',
        'Resources__ATTACHREL',
        'Routes__ATTACHREL',
        'Contacts__ATTACHREL',
        'Facilities_FacilityIDs',
        'Facilities_Incidents',
        'Facilities_ChemInvLocations',
        'Facilities_ScreeningAndScenarios',
        'Facilities_ContactsLink',
        'Facilities_Phone',
        'Facilities_SitePlanLink',
        'Facilities_MapData',
        'Incidents_IncidentMaterials',
        'Incidents_ContactsLink',
        'Incidents_SitePlanLink',
        'SpecialLocations_ContactsLink',
        'SpecialLocations_Phone',
        'SpecialLocations_SitePlanLink',
        'SpecialLocations_MapData',
        'Resources_ResourceEquipt',
        'Resources_ContactsLink',
        'Resources_Phone',
        'Resources_SitePlanLink',
        'Resources_MapData',
        'Routes_RouteIntersections',
        'Routes_Incidents',
        'Routes_ChemInvLocations',
        'Routes_ScreeningAndScenarios',
        'Routes_SitePlanLink',
        'Routes_MapData',
        'ChemInvLocations_ChemicalsInInventory',
        'ChemInvLocations_ChemInvMixtures',
        'Contacts_Phone',
        'Contacts_ContactsLink',
        'Contacts_SitePlanLink'
    ],
    "FeatureClasses" : {
        'Facilities': {
            'Count': 19,
            'Fields': [
                'OBJECTID',
                'Shape',
                'DateSigned',
                'DateTierIIReceived',
                'DikeOrOtherSafeguard',
                'FacilityDept',
                'FacilityName',
                'FacilityRecordID',
                'FailedValidation',
                'FCity',
                'FCountry',
                'FCounty',
                'FCrossStreet',
                'FDateModified',
                'FeesTotal',
                'FEmail',
                'FFireDistrict',
                'FMailAddress',
                'FMailCity',
                'FMailCountry',
                'FMailState',
                'FMailZip',
                'FNotes',
                'FState',
                'FStreetAddress',
                'FZip',
                'Latitude',
                'Longitude',
                'MSDSReceived',
                'MaxNumOccupants',
                'NumOfSites',
                'ReportYear',
                'Shipper',
                'SiteCoordAbbrev',
                'SiteMap',
                'SubjectToChemAccidentPrevention_Y',
                'SubjectToChemAccidentPrevention_N',
                'SubjectToEmergencyPlanning_Y',
                'SubjectToEmergencyPlanning_N',
                'Manned_Y',
                'Manned_N',
                'State01Checkbox',
                'State01Number',
                'State01Text',
                'State02Checkbox',
                'State02Number',
                'State02Text',
                'State03Checkbox',
                'State03Number',
                'State03Text',
                'State04Checkbox',
                'State04Text',
                'State05Checkbox',
                'State05Text',
                'State06Checkbox',
                'State06Text',
                'State07Checkbox',
                'State07Text',
                'State08Checkbox',
                'State08Text',
                'State09Checkbox',
                'SubmittedBy',
                'ThisSiteNum',
                'ValidationReport',
                'FacilityInfoSameAsLastYear',
                'State01Date',
                'State02Date'
            ]
        },
        'Incidents': {
            'Count': 2,
            'Fields': [
                'OBJECTID',
                'Shape',
                'ActionTaken',
                'CauseDescription',
                'CauseDumping',
                'CauseEquipment',
                'CauseNatural',
                'CauseOperational',
                'CauseOther',
                'CauseTransportation',
                'CauseUnknown',
                'Confidentiality',
                'CRID',
                'DischargerID',
                'DiscoveredDate',
                'DiscoveredTime',
                'EvacuationRequired',
                'FacilityRouteRecordID',
                'FollowupReceived',
                'FollowupRequired',
                'IncidentDischarge',
                'IncidentName',
                'IncidentRecordID',
                'InCity',
                'InCountry',
                'InCounty',
                'InDateModified',
                'InFireDistrict',
                'InLatitude',
                'InLongitude',
                'InNotes',
                'InState',
                'InStreetAddress',
                'InZip',
                'LocationReport',
                'MaterialOil',
                'MaterialOther',
                'MaterialUnknown',
                'MaterialHazardousSubstance',
                'MediumAir',
                'MediumGroundWater',
                'MediumLand',
                'MediumNone',
                'MediumOther',
                'MediumUnknown',
                'MediumWater',
                'MediumWithinFacility',
                'Milepost',
                'MultipleReports',
                'NotifiedAgency',
                'NotifiedDischarger',
                'NotifiedOther',
                'NotifiedStateLocal',
                'NotifiedUnknown',
                'NotifiedUSCG',
                'NRC',
                'NRCCaseID',
                'NumOfDeaths',
                'NumOfInjuries',
                'PropertyDamageGT50k',
                'RegionalCaseID',
                'ReportedDate',
                'ReportedTime',
                'ResponseAgency1',
                'ResponseAgency2',
                'ResponseAgency3',
                'ResponseAndEval',
                'ResponseType1',
                'ResponseType2',
                'ResponseType3',
                'RouteWaterwayName',
                'SourceAbvGrTank',
                'SourceAirTransport',
                'SourceFixedFacility',
                'SourceHighway',
                'SourceNumOfTanks',
                'SourceOffshore',
                'SourceOther',
                'SourcePipeline',
                'SourceRailway',
                'SourceTankCapacity',
                'SourceUndGrTank',
                'SourceUnknown',
                'SourceVehicleID',
                'SourceVessel',
                'SpillDate',
                'SpillTime',
                'SSIReport',
                'TankAmountUnits'
            ]
        },
        'Resources': {
            'Count': 1,
            'Fields': [
                'OBJECTID',
                'Shape',
                'ReCity',
                'ReCountry',
                'ReCounty',
                'ReDateModified',
                'ReEmail',
                'ReFireDistrict',
                'ReLatitude',
                'ReLongitude',
                'ReMailAddress',
                'ReMailCity',
                'ReMailCountry',
                'ReMailState',
                'ReMailZip',
                'ReNotes',
                'ResourceName',
                'ResourceRecordID',
                'ResourceType',
                'ReState',
                'ReStreetAddress',
                'ReZip',
                'FEMADiscipline',
                'FEMAResourceName',
                'FEMAType',
                'FEMAId',
                'FEMAStatus',
                'FEMAUpdated'
            ]
        },
        'SpecialLocations': {
            'Count': 1,
            'Fields': [
                'OBJECTID',
                'Shape',
                'AveAge',
                'AvePopulation',
                'BuildingType',
                'DailyMaxPopulation',
                'DailyMinPopulation',
                'SpNotes',
                'HoursOfOperation',
                'LocationName',
                'LocationType',
                'PeakSeason',
                'SeasonalMaxPopulation',
                'SeasonalMinPopulation',
                'SpCity',
                'SpCountry',
                'SpCounty',
                'SpCrossStreet',
                'SpDateModified',
                'SpecialLocRecordID',
                'SpEmail',
                'SpFireDistrict',
                'SpLatitude',
                'SpLongitude',
                'SpMailAddress',
                'SpMailCity',
                'SpMailCountry',
                'SpMailState',
                'SpMailZip',
                'SpState',
                'SpStreetAddress',
                'SpZip'
            ]
        }
    },
    "Tables" : {
        'ChemicalsInInventory':{
            'Count': 23,
            'Fields': [
                'OBJECTID',
                'Acute',
                'AveAmount',
                'AveAmountCode',
                'CBRecordID',
                'CFacilityRouteRecordID',
                'ChemInvRecordID',
                'ChemSameASLastYr',
                'Chronic',
                'CiCAS',
                'CiEHSChemical',
                'CiLastModified',
                'CiMSDS',
                'CiNotes',
                'DaysOnSite',
                'EnteredChemName',
                'Fire',
                'Gas',
                'Liquid',
                'MaxAmount',
                'MaxAmountCode',
                'MaxAmtContainer',
                'Mixture',
                'Pressure',
                'Pure',
                'Reactive',
                'Solid',
                'State01Checkbox',
                'State01Number',
                'State01Text',
                'State02Checkbox',
                'State02Number',
                'State02Text',
                'State03Checkbox',
                'State03Number',
                'State03Text',
                'State04Checkbox',
                'State04Number',
                'State04Text',
                'State05Checkbox',
                'State05Text',
                'State06Checkbox',
                'State06Text',
                'State07Checkbox',
                'State07Text',
                'State1ContactField',
                'State1ReqContact',
                'StateLabelCode',
                'TradeSecret',
                'BelowReportingThresholds',
                'ConfidentialStorageLocs',
                'Hazard_explosive',
                'Hazard_flammable',
                'Hazard_oxidizer',
                'Hazard_selfReactive',
                'Hazard_pyrophoricLiqSol',
                'Hazard_pyrophoricGas',
                'Hazard_selfHeating',
                'Hazard_organicPeroxide',
                'Hazard_corrosiveToMetal',
                'Hazard_gasUnderPressure',
                'Hazard_icwwEmitsFlammableGas',
                'Hazard_combustibleDust',
                'Hazard_acuteToxicity',
                'Hazard_skinCorrosion',
                'Hazard_seriousEyeDamage',
                'Hazard_respOrSkinSensitization',
                'Hazard_germCellMutagenicity',
                'Hazard_carcinogen',
                'Hazard_reprodToxicity',
                'Hazard_specTargOrgToxicity',
                'Hazard_aspirationHaz',
                'Hazard_simpleAsphyxiant',
                'Hazard_notOtherwiseClassified'
            ]
        },
        'ChemInvLocations': {
            'Count': 24,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'ChemInInvRecordID',
                'FacilityRouteRecordID',
                'Amount',
                'AmountUnit',
                'LocationType',
                'LocationPressure',
                'LocationTemperature',
                'Location',
                'LastModified'
            ]
        },
        'ChemInvMixtures': {
            'Count': 6,
            'Fields': [
                'OBJECTID',
                'MxChem',
                'RecordKey',
                'ChemInvRecID',
                'Percentage',
                'FacilityRouteRecordID',
                'MxCAS',
                'WtVol',
                'MxEHS',
                'MxLastModified',
                'MxMaxAmountCode'
            ]
        },
        'Contacts': {
            'Count': 5,
            'Fields': [
                'OBJECTID',
                'CoCity',
                'CoCountry',
                'CoCounty',
                'CoEmail',
                'CoFireDistrict',
                'CoMailAddress',
                'CoMailCity',
                'CoMailCountry',
                'CoMailState',
                'CoMailZip',
                'CoNotes',
                'Contact1Type',
                'Contact2Type',
                'Contact3Type',
                'Contact4Type',
                'ContactRecordID',
                'CoState',
                'CoStreetAddress',
                'CoZip',
                'FirstName',
                'LastName',
                'ModificationDate',
                'Organization',
                'Title',
                'DunAndBradstreet'
            ]
        },
        'ContactsLink': {
            'Count': 37,
            'Fields': [
                'OBJECTID',
                'ContactRecordID',
                'OtherRecordID',
                'RecordKey'
            ]
        },
        'FacilityIDs': {
            'Count': 6,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'FacilityRecordID',
                'Type',
                'Id',
                'Description',
                'LastModified'
            ]
        },
        'IncidentMaterials': {
            'Count': 1,
            'Fields': [
                'OBJECTID',
                'Chemical',
                'FacilityRouteRecordID',
                'IncidentRecordID',
                'LastModified',
                'QtyInWater',
                'QtyReleased',
                'QtyUnits',
                'QtyUnitsInWater',
                'RecordKey'
            ]
        },
        'MapData': {
            'Count': 1,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'ParentRecordID',
                'MARPLOTLayerName',
                'MARPLOTMapName',
                'MARPLOTMapID',
                'LastModified'
            ]
        },
        'Phone': {
            'Count': 33,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'ParentRecordID',
                'Phone',
                'Type',
                'PhLastModified'
            ]
        },
        'ResourceEquipt': {
            'Count': 1,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'ResourceRecordID',
                'ItemID',
                'Item',
                'Amount',
                'LastModified'
            ]
        },
        'RouteIntersections': {
            'Count': 2,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'RouteRecordID',
                'Order_',
                'Intersections',
                'LastModified'
            ]
        },
        'Routes': {
            'Count': 1,
            'Fields': [
                'OBJECTID',
                'RouteRecordID',
                'RouteName',
                'RouteType',
                'StartPoint',
                'EndPoint',
                'Evacuation',
                'Snow',
                'School',
                'MassTransit',
                'HAZMAT',
                'RoCounty',
                'RoFireDistrict',
                'TypesOfVehicles',
                'NumOfVehicles',
                'RoNotes',
                'RoDateModified'
            ]
        },
        'ScreeningAndScenarios': {
            'Count': 2,
            'Fields': [
                'OBJECTID',
                'ScenarioRecordID',
                'AmtReleased',
                'CBNumber',
                'ChemInvRecordID',
                'Concentration',
                'DikedArea',
                'FacilityRouteRecordID',
                'GroundRoughness',
                'LiquidStateType',
                'LOCType',
                'LOCValue',
                'PhysicalState',
                'Radius',
                'ReleaseDuration',
                'RiskConsequences',
                'RiskOfRelease',
                'RiskOverall',
                'ScDateModified',
                'ScNotes',
                'Screening',
                'ScreeningOrScenarioName',
                'SolidStateType',
                'StabilityClass',
                'WindFrom',
                'WindSpeed'
            ]
        },
        'SitePlanLink': {
            'Count': 25,
            'Fields': [
                'OBJECTID',
                'RecordKey',
                'FacilityRecordID',
                'Filename'
            ]
        },
        'Facilities__ATTACH': {
            'Count': 18,
            'Fields': [

            ]
        },
        'SpecialLocations__ATTACH': {
            'Count': 1,
            'Fields': [
                'ATTACHMENTID',
                'REL_OBJECTID',
                'CONTENT_TYPE',
                'ATT_NAME',
                'DATA_SIZE',
                'DATA'
            ]
        },
        'Incidents__ATTACH': {
            'Count': 1,
            'Fields': [
                'ATTACHMENTID',
                'REL_OBJECTID',
                'CONTENT_TYPE',
                'ATT_NAME',
                'DATA_SIZE',
                'DATA'
            ]
        },
        'Resources__ATTACH': {
            'Count': 1,
            'Fields': [
                'ATTACHMENTID',
                'REL_OBJECTID',
                'CONTENT_TYPE',
                'ATT_NAME',
                'DATA_SIZE',
                'DATA'
            ]
        },
        'Routes__ATTACH': {
            'Count': 1,
            'Fields': [
                'ATTACHMENTID',
                'REL_OBJECTID',
                'CONTENT_TYPE',
                'ATT_NAME',
                'DATA_SIZE',
                'DATA'
            ]
        },
        'Contacts__ATTACH': {
            'Count': 1,
            'Fields': [
                'ATTACHMENTID',
                'REL_OBJECTID',
                'CONTENT_TYPE',
                'ATT_NAME',
                'DATA_SIZE',
                'DATA'
            ]
        }
    }
}


def functional_tests(testSuite):
    #GEODATABASE TESTS***********************************************************
    print('Geodatabase Tests****************************************************')
    
    #Check to see if GDB exists
    test1 = arcpy.Exists(testSuite['GDBPath'])
    print("Geodatabase Exists: {}".format(test1))
    
    #Check to see if GDB is valid
    desc = arcpy.Describe(testSuite['GDBPath'])
    
    test2 = desc.dataType == 'Workspace'
    print("Geodatabase is Valid: {}".format(test2))
    
    test3 = desc.workspaceType == 'LocalDatabase'
    print("Geodatabase is a File Geodatabase: {}".format(test3))

    #Now that we know the GDB is valid change the workspace to the GDB
    arcpy.env.workspace = testSuite['GDBPath']

    #FEATURE CLASS TESTs*********************************************************
    print('\nFeature Class Tests**************************************************')

    #Check list of feature classes
    test4 = sorted(testSuite['FeatureClasses'].keys()) == sorted(arcpy.ListFeatureClasses())
    print("Expected Feature Classes Generated: {}".format(test4))

    #Check feature class counts and expected fields for each feature class
    for fcName, fcDict in testSuite['FeatureClasses'].items():
        
        actual = int(arcpy.management.GetCount(fcName)[0])
        expected = fcDict['Count']
        test5 = actual == expected
        print("Feature Class {}: \nExpected Count: {} | Actual Count: {} | {}".format(fcName, actual, expected, test5))
        
        test6 = sorted([field.name for field in arcpy.ListFields(fcName)]) == sorted(fcDict['Fields'])
        print("Feature Class {}: \nExpected Fields Created: {}".format(fcName,test6))

    print('\nTable Tests***********************************************************')        
    #Check list of tables
    test7 = sorted(testSuite['Tables'].keys()) == sorted(arcpy.ListTables())
    print("Expected Tables Generated: {}".format(test7))

    for tableName, tableDict in testSuite['Tables'].items():
        actual = int(arcpy.management.GetCount(tableName)[0])
        expected = tableDict['Count']
        test8 = actual == expected
        print("Table {}: \nExpected Count: {} | Actual Count: {} | {}".format(tableName, actual, expected, test8))
        
        test9 = sorted([field.name for field in arcpy.ListFields(tableName)]) == sorted(tableDict['Fields'])
        print("Table {}: \nExpected Fields Created: {}".format(tableName,test9))

    print('\nRelationship Classes Tests********************************************')
    #Check list of relationship classes
    test10 = sorted(testSuite['RelationshipClasses']) == sorted(next(arcpy.da.Walk(arcpy.env.workspace , datatype='RelationshipClass'))[2])
    print("Expected Relationship Classes Generated: {}".format(test10))


#arcpy.ImportToolbox(toolBoxPath)

#arcpy.cameo.ImportCameoData(mockCAMEOzip, testDir, "MockCAMEO")
functional_tests(mockCAMEO_expResults)
#arcpy.management.Delete(mockCAMEO_expResults['GDBPath'])


#arcpy.cameo.ImportCameoData(sampleCAMEOzip, testDir, "SampleCAMEO")
#arcpy.cameo.ImportCameoData([mockCAMEOzip, sampleCAMEO], "CombinedCAMEO")