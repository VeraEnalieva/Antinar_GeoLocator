import os
import glob
import re
from qgis.core import QgsProject



# USER_SETTINGS
dir = r'C:\_Workspace\TASK\Геокодирование\Отравления'
eas_buildings = 'buildings_EAS'
user_crs = 'ROJCRS["m64_1", BASEGEOGCRS["Pulkovo 1942", DATUM["Pulkovo 1942", ELLIPSOID["Krassowsky 1940",6378245,298.3, LENGTHUNIT["metre",1]], ID["EPSG",6284]], PRIMEM["Greenwich",0, ANGLEUNIT["Degree",0.0174532925199433]]], CONVERSION["unnamed", METHOD["Transverse Mercator", ID["EPSG",9807]], PARAMETER["Latitude of natural origin",0, ANGLEUNIT["Degree",0.0174532925199433], ID["EPSG",8801]], PARAMETER["Longitude of natural origin",30, ANGLEUNIT["Degree",0.0174532925199433], ID["EPSG",8802]], PARAMETER["Scale factor at natural origin",1, SCALEUNIT["unity",1], ID["EPSG",8805]], PARAMETER["False easting",95942.17, LENGTHUNIT["metre",1], ID["EPSG",8806]], PARAMETER["False northing",-6552810, LENGTHUNIT["metre",1], ID["EPSG",8807]]], CS[Cartesian,2], AXIS["(E)",east, ORDER[1], LENGTHUNIT["metre",1, ID["EPSG",9001]]], AXIS["(N)",north, ORDER[2], LENGTHUNIT["metre",1, ID["EPSG",9001]]]]'




os.chdir(dir)
#files_with_coord = glob.glob('*_coord.csv')
output_file = 'RESULT.gml'
# Выбирает из загруженных в проект!
names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
files_with_coord = []
for i in names:
    if re.findall('coord', i):
        files_with_coord.append(i)
    elif re.findall('_full', i):
        full_scr_tab = i
print(files_with_coord)

count = 0
tmp_lyrs = []
for f in files_with_coord:
    
    s1 = processing.run("native:fieldcalculator", 
                            {
                            'INPUT':f,
                            'FIELD_NAME':'long',
                            'FIELD_TYPE':0,
                            'FIELD_LENGTH':0,
                            'FIELD_PRECISION':8,
                            'FORMULA':' replace("Долгота", \',\', \'.\' )',
                            'OUTPUT':'TEMPORARY_OUTPUT'
                            })
                            
    s2 = processing.run("native:fieldcalculator", 
                        {
                        'INPUT':s1['OUTPUT'],
                        'FIELD_NAME':'lat',
                        'FIELD_TYPE':0,
                        'FIELD_LENGTH':0,
                        'FIELD_PRECISION':8,
                        'FORMULA':' replace("Широта", \',\', \'.\' )',
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })

    
    s3 = processing.run("native:createpointslayerfromtable", 
                    {
                    'INPUT':s2['OUTPUT'],
                    'XFIELD':'long',
                    'YFIELD':'lat',
                    'ZFIELD':'',
                    'MFIELD':'',
                    'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:4326'),
                    'OUTPUT':'TEMPORARY_OUTPUT'
                    })
                    
    s4 = processing.run("native:deletecolumn", 
                        {
                        'INPUT':s3['OUTPUT'],
                        'COLUMN':['Долгота','Широта'],
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })
                        
    s5 = processing.run("native:joinattributesbylocation", 
                        {
                        'INPUT':s4['OUTPUT'],
                        'PREDICATE':[5],
                        'JOIN':eas_buildings,
                        'JOIN_FIELDS':['ID_BUILDING_EAS', 'OKRUG_CODE', 'ОКАТО'],
                        'METHOD':0,
                        'DISCARD_NONMATCHING':False,
                        'PREFIX':'',
                        'OUTPUT':'TEMPORARY_OUTPUT'})
                        
    s6 = processing.run("native:joinattributestable", 
                        {
                        'INPUT':s5['OUTPUT'],
                        'FIELD':'set_id',
                        'INPUT_2':full_scr_tab,
                        'FIELD_2':'set_id',
                        'FIELDS_TO_COPY':[],
                        'METHOD':1,
                        'DISCARD_NONMATCHING':False,
                        'PREFIX':'',
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })
                        
    # QgsProject.instance().addMapLayer(s6['OUTPUT']).setName("NewLayer_"+str(count))
    count += 1 
    #iface.addVectorLayer(s3['OUTPUT'], "NewLayer", "ogr")
    tmp_lyrs.append(s6['OUTPUT'])
    
# Объединяем все новые слои в один
res1 = processing.run("native:mergevectorlayers", 
                    {
                    'LAYERS':tmp_lyrs,
                    'CRS':None,
                    'OUTPUT':'TEMPORARY_OUTPUT'
                    })
                    
res = processing.run("native:deletecolumn", 
                {
                'INPUT':res1['OUTPUT'],
                'COLUMN':['set_id_2','layer','path'],
                'OUTPUT':'TEMPORARY_OUTPUT'
                })                    

# QgsProject.instance().addMapLayer(res['OUTPUT']).setName("POINTS_"+str(count)+'lyrs')                    
processing.run("qgis:definecurrentprojection", 
                    {
                    'INPUT':res['OUTPUT'],
                    'CRS':QgsCoordinateReferenceSystem('EPSG:4326')
                    }
                    )
# Перепроецирование
msk_ver = processing.run("native:reprojectlayer", 
                {
                'INPUT':res['OUTPUT'],
                'TARGET_CRS':QgsCoordinateReferenceSystem('USER:100022'),
                #'TAGET_CRS': QgsCoordinateReferenceSystem(user_crs),
                'OPERATION':'', 
                'OUTPUT':'TEMPORARY_OUTPUT'
                })


eas_near = processing.run("native:joinbynearest", 
                {
                #'INPUT':QgsProcessingFeatureSourceDefinition(msk_ver['OUTPUT'], selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
                'INPUT':msk_ver['OUTPUT'],
                'INPUT_2':eas_buildings,
                'FIELDS_TO_COPY':['ID_BUILDING_EAS', 'ОКАТО', 'OKRUG_CODE'],
                'DISCARD_NONMATCHING':False,
                'PREFIX':'NEAR_',
                'NEIGHBORS':1,
                'MAX_DISTANCE':500,
                'OUTPUT':'TEMPORARY_OUTPUT'
                })

res1 = processing.run("native:fieldcalculator", 
                {
                'INPUT':eas_near['OUTPUT'],
                'FIELD_NAME':'ID_BUILDING_EAS',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':10,
                'FIELD_PRECISION':0,
                'FORMULA':'if("ID_BUILDING_EAS", "ID_BUILDING_EAS",  "NEAR_ID_BUILDING_EAS")',
                'OUTPUT':'TEMPORARY_OUTPUT'
                })
                
res2 = processing.run("native:fieldcalculator", 
                {
                'INPUT':res1['OUTPUT'],
                'FIELD_NAME':'OKRUG_CODE',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':10,
                'FIELD_PRECISION':0,
                'FORMULA':'if("OKRUG_CODE", "OKRUG_CODE",  "NEAR_OKRUG_CODE")',
                'OUTPUT':'TEMPORARY_OUTPUT'
                })  
  
res3 = processing.run("native:fieldcalculator", 
                {
                'INPUT':res2['OUTPUT'],
                'FIELD_NAME':'ОКАТО',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':10,
                'FIELD_PRECISION':0,
                'FORMULA':'if("ОКАТО", "ОКАТО",  "NEAR_ОКАТО")',
                'OUTPUT':'TEMPORARY_OUTPUT'
                })  
                
addxy = processing.run("native:addxyfields", 
                        {
                        'INPUT':res3['OUTPUT'],
                        'CRS':QgsCoordinateReferenceSystem('USER:100022'),
                        'PREFIX':'',
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })
                        
result = processing.run("native:deletecolumn", 
                        {
                        'INPUT':addxy['OUTPUT'],
                        'COLUMN':['n','feature_x','feature_y','nearest_x','nearest_y'],
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })                        

join_mo_name = processing.run("native:joinattributestable", 
                {
                'INPUT':result['OUTPUT'],
                'FIELD':'OKRUG_CODE',
                'INPUT_2':'MO_okrug',
                'FIELD_2':'Номер',
                'FIELDS_TO_COPY':['Название'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':'TEMPORARY_OUTPUT'
                }
                )
QgsProject.instance().addMapLayer(join_mo_name['OUTPUT']).setName("Result")

export_gml = processing.run("native:refactorfields", 
                            {
                            'INPUT':join_mo_name['OUTPUT'],
                            'FIELDS_MAPPING':[
                                {'expression': '"set_id"','length': 20,'name': 'OBJECTID_1','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"set_id"','length': 20,'name': 'OBJECTID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"ID_BUILDING_EAS"','length': 10,'name': 'ID_EAS','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"adr_src"','length': 0,'name': 'adress_in_','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"x"','length': 20,'name': 'X','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                {'expression': '"y"','length': 20,'name': 'Y','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                {'expression': 'if("HouseNum", array_to_string(array("Street","HouseNum"), \', \'), "Street")','length': 0,'name': 'Adress','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': ' string_to_array((string_to_array("adr_src", \', \')[-1]), \' \')[0]','length': 0,'name': 'District','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"Age"','length': 0,'name': 'Age','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"SocialGr"','length': 0,'name': 'SocialGr','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"Sex"','length': 0,'name': 'Sex','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"set_id"','length': 20,'name': 'ID','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"Street"','length': 250,'name': 'Street','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"HouseNum"','length': 0,'name': 'HouseNum','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"Mesto"','length': 0,'name': 'Mesto','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"Data"','length': 0,'name': 'Data','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"Diagnoz"','length': 0,'name': 'Diagnoz','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"MstSmert"','length': 0,'name': 'MstSmert','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"HarOtrvl"','length': 0,'name': 'HarOtrvl','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"KolOtrvl"','length': 0,'name': 'KolOtrvl','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"ObstOtr"','length': 250,'name': 'ObstOtr','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"MestKupl"','length': 250,'name': 'MestKupl','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"ОКАТО"','length': 10,'name': 'OkatoD','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"Название"','length': 250,'name': 'MO','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'}
                                ],
                            'OUTPUT':output_file
                            }
                            )

# QgsProject.instance().addMapLayer(export_gml['OUTPUT'])
#output_file = QgsVectorLayer(os.path.abspath(output_file))
iface.addVectorLayer(output_file, "Result_GML", "ogr")

print('Ready')