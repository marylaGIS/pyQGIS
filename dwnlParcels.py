'''
download parcels from ULDK service without running QGIS
pycharm configuration:
https://anitagraser.com/2019/03/03/stand-alone-pyqgis-scripts-with-osgeo4w/
'''

import sys, requests
from qgis.core import *
from qgis.analysis import *
from PyQt5.QtCore import QVariant

# initializing QGIS
# change the path to the appropriate one
QgsApplication.setPrefixPath(r'C:\OSGeo4W64\apps\qgis', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# add path to processing so we can import it next
sys.path.append(r'C:\OSGeo4W64\apps\qgis\python\plugins')
# import processing after! initializing QGIS
import processing
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
feedback = QgsProcessingFeedback()

# create a list with parcels id's from the external file
'''
sample file structure:
146502_8.1302.9/13
146502_8.1302.13/1
146502_8.1302.13/2
'''
# change path to your local file
parcels = []
with open(r'C:\Users\User\Desktop\parcels.txt') as file:
    for line in file:
        parcels.append(line.rstrip())

# create a list with ULDK urls based on a list with parcel ids created above
urls = []
for p in parcels:
    urls.append(f'https://uldk.gugik.gov.pl/?request=GetParcelById&id={p}&result=geom_wkt')

# create a list with ULDK responses containing parcel geometry in wkt format
responses = []
for u in urls:
    r = requests.get(u)
    # responses.append(r)
    # if the parcel is not found, save its id to a file
    if r.text[:2] == '-1':
        with open('missing_parcels.txt', 'a') as missing:
            missing.write(u[52:-16] + '\n')
    else:
        responses.append(r)

# create a vector layer with parcel id field
layer = QgsVectorLayer('Polygon?crs=epsg:2180', 'dzialki', 'memory')
pr = layer.dataProvider()
pr.addAttributes([QgsField('TERYT', QVariant.String)])
layer.updateFields()

# for every response create a vector feature
# with geometry from responses's wkt
# and parcel's id - teryt (as a substring from response url)
for r in responses:
    poly = QgsFeature()
    geom = QgsGeometry.fromWkt(r.text.split(';')[1])
    poly.setGeometry(geom)
    poly.setAttributes([f'{r.url[52:-16]}'])
    pr.addFeatures([poly])
    layer.updateExtents()

#QgsProject.instance().addMapLayers([layer])

# use QGIS processing script to create geopackage with the data
# change the path to the appropriate one
processing.run("native:package", {'LAYERS':layer,
                                  'OUTPUT':'C:/Users/User/Desktop/dzialki.gpkg',
                                  'OVERWRITE':False,
                                  'SAVE_STYLES':False})

qgs.exitQgis()
