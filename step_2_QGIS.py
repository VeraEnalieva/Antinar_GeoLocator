import os
import glob
import re
from qgis.core import QgsProject



# USER_SETTINGS
dir = r'C:\_Workspace\TASK\Геокодирование\Сообщения'
eas_buildings = 'buildings_EAS'





os.chdir(dir)
#files_with_coord = glob.glob('*_coord.csv')

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
                        'JOIN_FIELDS':['ID_BUILDING_EAS'],
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

QgsProject.instance().addMapLayer(res['OUTPUT']).setName("POINTS_"+str(count)+'lyrs')                    

print('Ready')