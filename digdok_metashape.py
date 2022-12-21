# Fully automated photogrammetry workflow using Agisoft Metashape's python librares
#
# Written by Hallvard R. Indgjerd, 18.12.2022
# 
# Based on code from James Herbst, 2016, and Hallvard Indgjerd 2021/2022 
# Input on optimisation values from the Universitetssenteret paa Svalbard's Geo-SfM course: https://unisvalbard.github.io/Geo-SfM/content/lessons/l1/tutorial.html and the USGS SfM Workflow documentation: https://pubs.usgs.gov/of/2021/1039/ofr20211039.pdf

import sys
import os
from datetime import datetime
import Metashape
import math

# Variables
doc = Metashape.app.document
found_major_version = ".".join(Metashape.app.version.split('.')[:2])
csv = Metashape.ReferenceFormatCSV #format of file is comma delimited

##Selection Percentages
RU_Percent = 20
PA_Percent = 20
RE_Percent = 20

## Selection Thresholds
RU_Threshold = 10
PA_Threshold = 5
RE_Threshold = 0.9

def pickfoldernamechunk():
  # Create a new chunk named from a selected a folder and add all photos from that folder

  #Select folder
  path = Metashape.app.getExistingDirectory("Select root folder for projects.")
  backslash = "/" # Metashape now uses slash (/) not backslash (\).
  print (path) #display full path and folder name in console
  bkslno = path.rfind(backslash)+1
  pathlen = len(path)
  folders = os.listdir(path)
  for folder in folders:
    folderpath = os.path.join(path,folder)
    if os.path.isdir(folderpath):
      print ('Create new chunk named "' + folder + '"')
      #create new chunk named after folder
      chunk = doc.addChunk()
      chunk.label = folder

      #load all images from specified folder into new chunk
      image_list = os.listdir(folderpath + "/Photos")
      photo_list = list()
      for photo in image_list:
        if ("jpg" or "jpeg" or "JPG" or "JPEG") in photo.lower():
          photo_list.append(folderpath + "/Photos/" + photo)
      chunk.addPhotos(photo_list)

  #remove empty chunks
  for chunk in list(doc.chunks):
    if not len(chunk.cameras):
      doc.remove(chunk)
  
  #save project
  camera = chunk.cameras[0]
  date = datetime.strptime(camera.photo.meta["Exif/DateTimeOriginal"], '%Y:%m:%d %H:%M:%S')
  #area = Metashape.app.getString(label = "Area mapped (for filename):", value = "Room")
  project_name = folder + "_" + date.strftime("%d%m%y") + ".psx"
#  doc.save(path + "/" + project_name)
    
#-----------------------------------------------------------------

# Calculate image quality and disable images with quality less than a specified variable.
def estimagequality():

    # Calculate image quality and disable images with quality less than a specified variable.
  #chunk = doc.chunk
    
  tlabel = 'Quality theshold'
  #threshold = Metashape.app.getFloat(tlabel, value=0.6) # photos with image quality below this amount will be disabled.
  threshold = 0.6

  for chnk in doc.chunks:
    #camera = chnk.cameras
    #chnk.estimateImageQuality(camera)
    camerasniq = [camera for camera in chnk.cameras
      if 'Image/Quality' not in camera.meta]

    if len(camerasniq) > 0:
      print('Test OK!')
      print(found_major_version)
      if found_major_version == '1.5':
        chnk.estimateImageQuality(camerasniq)
      else:
        chnk.analyzePhotos(camerasniq)

    for i in range(0, len(chnk.cameras)):
      print('photo ' + str(i))
      camera = chnk.cameras[i]
      print(camera)
      quality = float(camera.meta['Image/Quality'])
      print(str(quality))
      if quality < threshold:
        camera.enabled = False
    #doc.save()
   
  mlabel = 'Photos with image quality less than ' + str(threshold) + ' disabled. Project saved.'
  #Metashape.app.messageBox(mlabel)     # display msgbox when done
  print(mlabel)
  
# -----------------------------------------------------------------------
def align():
  for chnk in Metashape.app.document.chunks:
    chnk.detectMarkers()
    chnk.matchPhotos(keypoint_limit = 40000, tiepoint_limit = 10000, generic_preselection = True, reference_preselection = True)
    chnk.alignCameras()
    #doc.save()
    
# -----------------------------------------------------------------------

def cpoptargets():
    # defines path to target.txt file and the format of the file.  Makes a srting list of markers detected, then a range of markers up. Finally imports the target.txt file.


  #path = Metashape.app.getOpenFileName("Get the comma delimited target.txt file (name,x,y,z)")     # Path to the folder
  folderpath = Metashape.app.getExistingDirectory("Select root folder for projects.")
  format = Metashape.ReferenceFormatCSV #format of file is comma delimited

  for chnk in doc.chunks:

    targetfile = folderpath + "/" + chnk.label + "/targets.txt"     # Path to the folder
    #chunk = doc.chunk

    chnk.crs = Metashape.CoordinateSystem("EPSG::32630")		#Change to get from DB

    MarkersList = str(list(chnk.markers))                            # strings a list of class markers.
    print (MarkersList)                                              # display list of detected targets in console.

    if found_major_version == '1.5':
      chnk.loadReference(targetfile, csv, columns='nxyz', delimiter=',', skip_rows=0) #import coord values.
    else:
      chnk.importReference(targetfile, csv, columns='nxyz', delimiter=',', skip_rows=0) #import coord values.
    chnk.updateTransform()
    #doc.save()  
#--------------------------------------------------------------------------------

#uncheckmarkers #unchecks markers in a chunk with two or fewer projections.
def uncheckmarkers():

  #unchecks markers in a chunk with two or fewer projections.
  for chnk in doc.chunks:

    for i in range(0, len(chnk.markers)):
      marker = chnk.markers[i]
      print(marker)
      noproj = len(marker.projections)
      print(str(noproj))
      if noproj < 3:
        marker.reference.enabled = False
        print(str(marker) + " disabled.")
        
    #doc.save()
    print('All markers with fewer than 3 projections unchecked in chunk ' + chnk.label + '. Project saved.')

# -----------------------------------------------------------------------
#alignbb2cs Aligns bounding boxes of all chunks to the grid
def alignbb2cs():

  for chnk in doc.chunks:
    T = chnk.transform.matrix
    v_t = T * Metashape.Vector( [0,0,0,1] )
    v_t.size = 3
    if chnk.crs:
      m = chnk.crs.localframe(v_t)
    else:
      m = Metashape.Matrix().diag([1,1,1,1])
    m = m * T
    s = math.sqrt(m[0,0] ** 2 + m[0,1] ** 2 + m[0,2] ** 2) #scale factor
    R = Metashape.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])
    R = R * (1. / s)
    reg = chnk.region
    reg.rot = R.t()
    chnk.region = reg
  print("All bounding boxes aligned to grid")
    
#--------------------------------------------------------------------------------

#Optimize alignemnts
def optimizealignments():

  for chnk in doc.chunks:
    if found_major_version == '1.5': # Haven't cheked older versions, both the same for now
      chnk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=False, fit_b2=False, fit_k1=True, fit_k2=True, fit_k3=True, fit_k4=False, fit_p1=True, fit_p2=True, fit_corrections=False, adaptive_fitting=False, tiepoint_covariance=True)
    else:
      chnk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=False, fit_b2=False, fit_k1=True, fit_k2=True, fit_k3=True, fit_k4=False, fit_p1=True, fit_p2=True, fit_corrections=False, adaptive_fitting=False, tiepoint_covariance=True)
        
    #doc.save()
    print('Camera positions optimised for chunk ' + chnk.label + '. Project saved.')
    
#--------------------------------------------------------------------------------
#Error reduction - Reconstruction Uncertainty
def reconstructionuncertainty():

  for chnk in doc.chunks:
    if found_major_version == '1.5': 
      continue
    else:
      points = chnk.point_cloud.points
      filter = Metashape.PointCloud.Filter()
      filter.init(chnk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty) #Reconstruction Uncertainty
      list_values = filter.values
      list_values_valid = list()
      StartPoints = len(list_values_valid)

      for i in range(len(list_values)):
        if points[i].valid:
          list_values_valid.append(list_values[i])
      list_values_valid.sort()
      target = int(len(list_values_valid) * RU_Percent / 100)
      StartPoints = int(len(list_values_valid))
      threshold = list_values_valid[target]
      if (threshold < RU_Threshold):
        threshold = RU_Threshold
      filter.selectPoints(threshold)
      filter.removePoints(threshold)

      print("")
      print("Error Reduction Report for chunk" + chnk.label + ":")
      RU_actual_threshold = threshold
      print(str(threshold) + " threshold reached")
      print(str(StartPoints) + " points at start")
      print(str(target) + " points removed")
      print("Reconstruction Uncertainty filter completed")
      print("")
    #doc.save()

#--------------------------------------------------------------------------------
#Error reduction - Projection Accuracy
def projectionaccuracy():

  for chnk in doc.chunks:
    if found_major_version == '1.5': 
      continue
    else:
      points = chnk.point_cloud.points
      filter = Metashape.PointCloud.Filter()
      filter.init(chnk, criterion = Metashape.PointCloud.Filter.ProjectionAccuracy) #Projection Accuracy
      list_values = filter.values
      list_values_valid = list()

      for i in range(len(list_values)):
        if points[i].valid:
          list_values_valid.append(list_values[i])
      list_values_valid.sort()
      target = int(len(list_values_valid) * PA_Percent / 100)
      StartPoints = int(len(list_values_valid))
      threshold = list_values_valid[target]
      if (threshold < PA_Threshold):
        threshold = PA_Threshold
      filter.selectPoints(threshold)
      filter.removePoints(threshold)

      print("")
      print("Error Reduction Report for chunk" + chnk.label + ":")
      PA_actual_threshold = threshold
      print(str(threshold) + " threshold reached")
      print(str(StartPoints) + " points at start")
      print(str(target) + " points removed")
      print("Projection Accuracy filter completed")
      print("")
    #doc.save()
    
#--------------------------------------------------------------------------------
#Error reduction - Reprojection Error
def reconstructionuncertainty():

  for chnk in doc.chunks:
    if found_major_version == '1.5': 
      continue
    else:
      points = chnk.point_cloud.points
      filter = Metashape.PointCloud.Filter()
      filter.init(chnk, criterion = Metashape.PointCloud.Filter.ReprojectionError) #Reprojection Error
      list_values = filter.values
      list_values_valid = list()

      for i in range(len(list_values)):
        if points[i].valid:
          list_values_valid.append(list_values[i])
      list_values_valid.sort()
      target = int(len(list_values_valid) * RE_Percent / 100)
      StartPoints = int(len(list_values_valid))
      threshold = list_values_valid[target]
      if (threshold < RE_Threshold):
        threshold = RE_Threshold
      filter.selectPoints(threshold)
      filter.removePoints(threshold)

      print("")
      print("Error Reduction Report for chunk" + chnk.label + ":")
      RE_actual_threshold = threshold
      print(str(threshold) + " threshold reached")
      print(str(StartPoints) + " points at start")
      print(str(target) + " points removed")
      print("Reprojection Error filter completed")
      print("")
    #doc.save()        
#--------------------------------------------------------------------------------
#Build Depth Maps
# This step could benefit from calibration..
# - Check witch filter level is better for objects. 
# - Unsure about values for max neighbours (try 100 or -1), workitem size and max workgroup size.
#
# Note:
#	For depth maps quality the downscale correspondence should be the following:
#	Ultra = 1
#	High = 2
#	Medium = 4
#	Low = 8
#	Lowest = 16
#

def builddepthmaps():

  for chnk in doc.chunks:
    if found_major_version == '1.5':
      chnk.buildDepthMaps(quality= HighQuality, filter=ModerateFiltering, reuse_depth=True)
    else:
      chnk.buildDepthMaps(downscale=2, filter_mode=Metashape.ModerateFiltering, reuse_depth=True, max_neighbors=16, subdivide_task=True, workitem_size_cameras=20, max_workgroup_size=100)
        
    #doc.save()
    print('Depth maps created for chunk ' + chnk.label + '. Project saved.')    
           
pickfoldernamechunk()
estimagequality()
align()
cpoptargets()
uncheckmarkers()
alignbb2cs()
optimizealignments()
reconstructionuncertainty()
optimizealignments()
projectionaccuracy()
optimizealignments()
reconstructionuncertainty()
optimizealignments()
builddepthmaps()
