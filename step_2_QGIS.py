import os
import glob
import re
from qgis.core import QgsProject



# USER_SETTINGS
source_file = r'C:\_Workspace\TASK\Геокодирование\Отравления_3кв_2023.xlsx'
eas_buildings ='Здания ЕАС'
d_adm = 'Районы Города'
mo_okrug = 'Муниципальные Округа'
usercrs = 'PROJCRS["m64_1", BASEGEOGCRS["Pulkovo 1942", DATUM["Pulkovo 1942", ELLIPSOID["Krassowsky 1940",6378245,298.3, LENGTHUNIT["metre",1]], ID["EPSG",6284]], PRIMEM["Greenwich",0, ANGLEUNIT["Degree",0.0174532925199433]]], CONVERSION["unnamed", METHOD["Transverse Mercator", ID["EPSG",9807]], PARAMETER["Latitude of natural origin",0, ANGLEUNIT["Degree",0.0174532925199433], ID["EPSG",8801]], PARAMETER["Longitude of natural origin",30, ANGLEUNIT["Degree",0.0174532925199433], ID["EPSG",8802]], PARAMETER["Scale factor at natural origin",1, SCALEUNIT["unity",1], ID["EPSG",8805]], PARAMETER["False easting",95942.17, LENGTHUNIT["metre",1], ID["EPSG",8806]], PARAMETER["False northing",-6552810, LENGTHUNIT["metre",1], ID["EPSG",8807]]], CS[Cartesian,2], AXIS["(E)",east, ORDER[1], LENGTHUNIT["metre",1, ID["EPSG",9001]]], AXIS["(N)",north, ORDER[2], LENGTHUNIT["metre",1, ID["EPSG",9001]]]]'


dir = os.path.dirname(source_file)
basename = (os.path.basename(source_file)).split('.')[0]
os.chdir(dir)
#files_with_coord = glob.glob('*_coord.csv')
output_file = 'RESULT2.gml'

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
    # формирование пространственного слоя из текстовых данных
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

    # Присоединение подробностей происшествий из исходных данных                        
    s6 = processing.run("native:joinattributestable", 
                        {
                        'INPUT':s4['OUTPUT'],
                        'FIELD':'set_id',
                        'INPUT_2':full_scr_tab,
                        'FIELD_2':'set_id',
                        'FIELDS_TO_COPY':[],
                        'METHOD':1,
                        'DISCARD_NONMATCHING':False,
                        'PREFIX':'',
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })
                        
    count += 1 
    tmp_lyrs.append(s6['OUTPUT'])
    
# Обединение всех входящих данных в один пространсвенный слой
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


# Явное указние текущей СК
processing.run("qgis:definecurrentprojection", 
                    {
                    'INPUT':res['OUTPUT'],
                    'CRS':QgsCoordinateReferenceSystem('EPSG:4326')
                    }
                    )

# Добавление координат в МСК-64                
addxy = processing.run("native:addxyfields", 
                        {
                        'INPUT':res['OUTPUT'],
                        'CRS':QgsCoordinateReferenceSystem(usercrs),
                        'PREFIX':'',
                        'OUTPUT':'TEMPORARY_OUTPUT'
                        })
                        
result = processing.run("native:deletecolumn", 
            {
            'INPUT':addxy['OUTPUT'],
            'COLUMN':['n','feature_x','feature_y','nearest_x','nearest_y'],
            'OUTPUT':'TEMPORARY_OUTPUT'
            })    

# Присоединение ID_EAS    

eas_near = processing.run("native:joinbynearest", 
            {
            'INPUT':result['OUTPUT'],
            'INPUT_2': eas_buildings,
            'FIELDS_TO_COPY':['ID_BUILDING_EAS','PADDRESS','HOUSE','CORPUS','LITER','ОКАТО','OKRUG_CODE'],
            'DISCARD_NONMATCHING':False,
            'PREFIX':'EAS_',
            'NEIGHBORS':1,
            'MAX_DISTANCE':None,
            'OUTPUT':'TEMPORARY_OUTPUT'
            })
                    

# Добавление названия муниципального округа по кодам
join_mo_name = processing.run("native:joinattributestable", 
                {
                'INPUT':eas_near['OUTPUT'],
                'FIELD':'EAS_OKRUG_CODE',
                'INPUT_2':mo_okrug,
                'FIELD_2':'Номер',
                'FIELDS_TO_COPY':['Название'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':'TEMPORARY_OUTPUT'
                }
                )


# Формирование порядкового номера                
objectid_auto = processing.run("native:addautoincrementalfield", 
            {
            'INPUT':join_mo_name['OUTPUT'],
            'FIELD_NAME':'AUTO',
            'START':1,
            'MODULUS':0,
            'GROUP_FIELDS':[],
            'SORT_EXPRESSION':'',
            'SORT_ASCENDING':True,
            'SORT_NULLS_FIRST':False,
            'OUTPUT':'TEMPORARY_OUTPUT'
            })

join_d_adm = processing.run("native:joinattributesbylocation", 
                        {
                        'INPUT':objectid_auto['OUTPUT'],
                        'PREDICATE':[5],
                        'JOIN':d_adm,
                        'JOIN_FIELDS':['Name'],
                        'METHOD':0,
                        'DISCARD_NONMATCHING':False,
                        'PREFIX':'',
                        'OUTPUT':'TEMPORARY_OUTPUT'})


# Маркирование сомнительной привязки
pay_attencion = processing.run("native:fieldcalculator", 
                        {
                            'INPUT':join_d_adm['OUTPUT'],
                            'FIELD_NAME':'PAY_AT',
                            'FIELD_TYPE':6,
                            'FIELD_LENGTH':1,
                            'FIELD_PRECISION':0,
                            'FORMULA':'if(("distance"*35000 > 10) OR ("HouseNum" =\'\') OR (string_to_array((string_to_array("adr_src", \', \')[-1]), \' \')[0] <> "Name"), False, True)',
                            'OUTPUT':'TEMPORARY_OUTPUT'
                            })

                
QgsProject.instance().addMapLayer(pay_attencion['OUTPUT']).setName("Result")

export_gml = processing.run("native:refactorfields", 
                            {
                            'INPUT':pay_attencion['OUTPUT'],
                            'FIELDS_MAPPING':[
                                {'expression': '"AUTO"','length': 0,'name': 'OBJECTID_1','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"AUTO"','length': 0,'name': 'OBJECTID','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"EAS_ID_BUILDING_EAS"','length': 10,'name': 'ID_EAS','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"adress_in_"','length': 0,'name': 'adress_in_','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"adr_src"','length': 0,'name': 'adr_src','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"x"','length': 20,'name': 'X','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                {'expression': '"y"','length': 20,'name': 'Y','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                {'expression': 'if("HouseNum", array_to_string(array("Street","HouseNum"), \', \'), "Street")','length': 0,'name': 'Adress','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': 'string_to_array((string_to_array("adr_src", \', \')[-1]), \' \')[0]','length': 0,'name': 'District','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
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
                                {'expression': '"EAS_ОКАТО"','length': 10,'name': 'OkatoD','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                                {'expression': '"Название"','length': 250,'name': 'MO','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                
                                {'expression': '"n"','length': 0,'name': 'FOUND_CONT','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                # пересчёт расстояния из градусов в метры. Очень приблизительный, но в этой задаче расстояние служит скорее маркером. Норм
                                {'expression': 'round("distance"*35000, 2)','length': 0,'name': 'distance','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'}, 
                                {'expression': '"EAS_PADDRESS"','length': 250,'name': 'EAS_PADDRESS','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"EAS_HOUSE"','length': 250,'name': 'EAS_HOUSE','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"EAS_CORPUS"','length': 250,'name': 'EAS_CORPUS','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"EAS_LITER"','length': 250,'name': 'EAS_ LITER','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"Name"','length': 250,'name': 'FACT_RAYON','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                {'expression': '"PAY_AT"','length': 1,'name': 'PAY_ATTENTION','precision': 0,'sub_type': 0,'type': 1,'type_name': 'boolean'}
                                ],
                            'OUTPUT':output_file
                            }
                            )

# QgsProject.instance().addMapLayer(export_gml['OUTPUT'])
#output_file = QgsVectorLayer(os.path.abspath(output_file))
iface.addVectorLayer(output_file, basename, "ogr")

print('Ready')