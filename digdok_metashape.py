#!/usr/bin/python
#
# Fully automated photogrammetry workflow using Agisoft Metashape's python librares
#
# Written by Hallvard R. Indgjerd, 18.12.2022
# 
# Based on code from James Herbst, 2016, and Hallvard Indgjerd 2021/2022 
# Input on optimisation values from the Universitetssenteret paa Svalbard's Geo-SfM course: https://unisvalbard.github.io/Geo-SfM/content/lessons/l1/tutorial.html and the USGS SfM Workflow documentation: https://pubs.usgs.gov/of/2021/1039/ofr20211039.pdf

import sys
import os
import glob
import argparse
from datetime import datetime, date
import Metashape
import pymeshlab
import psycopg2
from dbconfig import config
import math
import csv
import json
import subprocess

# Variables
# doc = Metashape.app.document
doc = Metashape.Document()
version = Metashape.app.version
found_major_version = ".".join(version.split('.')[:2])
csvformat = Metashape.ReferenceFormatCSV #format of file is comma delimited

#Modes: db, standalone
#mode = "db" 

def vars(uuid):
  # Declaring vars as global:
  global setting_group
  ## Workflow
  global est_iq_bool
  global align_bool
  global poptargets_bool
  global uncheckmarkers_bool
  global scalebar_bool
  global alignbbox_bool
  global optimizealignment_bool
  global err_red_bool
  global depthmap_bool
  global densecloud_bool
  global mesh_bool
  global texture_bool
  global dem_bool
  global ortho_bool
  ## Image quality
  global iq_threshold
  ## Error correction Percentages
  global RU_Percent
  global PA_Percent
  global RE_Percent
  ## Error correction Thresholds
  global RU_Threshold
  global PA_Threshold
  global RE_Threshold
  ## Depthmaps settings
  global depthmap_quality
  global depthmap_filter
  ## CRS
  global crs
  ## Image alignment settings
  global keypoint_limit
  global tiepoint_limit
  global generic_preselection_bool
  global reference_preselection_bool
  ## UV and Texture settings
  global uv_pages
  global texture_size
  global ghosting_filter_bool
  global blending_mode
  global texture_type
  global fill_holes_bool
  ## Model/mesh settings
  global surface_type
  global interpolation
  global face_count_custom
  global source_data
  global vertex_colors_bool
  global vertex_confidence_bool
  ##DEM settings
  global dem_datasource
  global dem_interpolation
  global dem_resolution
  global dem_params
  ## Orthos settings
  global ortho_surfacedata
  global ortho_blending_mode
  global ortho_fill_holes_bool
  global ortho_ghosting_filter_bool
  global ortho_cull_faces_bool
  global ortho_refine_seamlines_bool
  global ortho_resolution
  ## Export settings
  global export_bool
  global short_coords
  global export_formats


  # If db mode, get vars from DB
  if mode == "db":
    query = (
      "SELECT settings.*"
      "FROM new.process_settings settings "
      "JOIN new.process_status proc ON proc.settings_uuid = settings.uuid "
      "WHERE proc.uuid = '" + uuid + "';"
      )
    settings = dbconnection(query, "select_one")
  
    print("Settings retrieved: ")
    print(settings)
  
    setting_group = settings[1]
  
    ## Workflow
    est_iq_bool = settings[2]
    align_bool = settings[3]
    poptargets_bool = settings[4]
    uncheckmarkers_bool = settings[5]
    scalebar_bool = settings[52]
    alignbbox_bool = settings[6]
    optimizealignment_bool = settings[7]
    err_red_bool = settings[8]
    depthmap_bool = settings[9]
    densecloud_bool = settings[10]
    mesh_bool = settings[11]
    texture_bool = settings[12]
    dem_bool = settings[13]
    ortho_bool = settings[14]
  
    ## Image quality
    iq_threshold = settings[15]
  
    ## Error correction Percentages
    RU_Percent = settings[16]
    PA_Percent = settings[17]
    RE_Percent = settings[18]
  
    ## Error correction Thresholds
    RU_Threshold = settings[19]
    PA_Threshold = settings[20]
    RE_Threshold = settings[21]
  
    ## Depthmaps settings
    depthmap_quality = settings[22]
    depthmap_filter = settings[23]
  
    ## CRS
    crs = settings[24]
  
    ## Image alignment settings
    keypoint_limit = settings[25]
    tiepoint_limit = settings[26]
    generic_preselection_bool = settings[27]
    reference_preselection_bool = settings[28]

    ## UV and Texture settings
    uv_pages = settings[29]
    texture_size = settings[30]
    ghosting_filter_bool = settings[31]
    blending_mode = settings[32]
    texture_type = settings[33]
    fill_holes_bool = settings[34]

    ## Model/mesh settings
    surface_type = settings[35]
    interpolation = settings[36]
    face_count_custom = settings[37]
    source_data = settings[38]
    vertex_colors_bool = settings[39]
    vertex_confidence_bool = settings[40]

    ##DEM settings
    dem_datasource = settings[41]
    dem_interpolation = settings[42]
    dem_resolution = settings[43]
    dem_params = settings[55]

    ## Orthos settings
    ortho_surfacedata = settings[44]
    ortho_blending_mode = settings[45]
    ortho_fill_holes_bool = settings[46]
    ortho_ghosting_filter_bool = settings[47]
    ortho_cull_faces_bool = settings[48]
    ortho_refine_seamlines_bool = settings[49]
    ortho_resolution = settings[50]

    ## Export settings
    export_bool = settings[51]
    short_coords = settings[53]
    export_formats = settings[54]


  # If standalone mode, set vars here 
  else:
    setting_group = "Default manual settings (HRI 27.12.22)"

    ## Workflow
    est_iq_bool = True
    align_bool = True
    poptargets_bool = True
    uncheckmarkers_bool = True
    scalebar_bool = True
    alignbbox_bool = True
    optimizealignment_bool = True
    err_red_bool = True
    depthmap_bool = True
    densecloud_bool = False
    mesh_bool = True
    texture_bool = True
    dem_bool = True
    ortho_bool = True
  
    ## Image quality
    iq_threshold = 0.6
  
    ## Error correction Percentages
    RU_Percent = 20
    PA_Percent = 20
    RE_Percent = 20
  
    ## Error correction Thresholds
    RU_Threshold = 10
    PA_Threshold = 5
    RE_Threshold = 0.9
  
    ## CRS
    crs = 32630
  
    ## Image alignment settings
    keypoint_limit = 40000
    tiepoint_limit = 10000
    generic_preselection_bool = True
    reference_preselection_bool = True

    ## UV and Texture settings
    uv_pages = 2
    texture_size = 4096
    ghosting_filter_bool = True
    blending_mode = "MosaicBlending"
    texture_type = "DiffuseMap"
    fill_holes_bool = True

    ## Model/mesh settings
    surface_type = "Arbitrary"
    interpolation = "EnabledInterpolation"
    face_count_custom = 0
    source_data = "DepthMapsData"
    vertex_colors_bool = True
    vertex_confidence_bool = True

    ## DEM settings
    dem_datasource = "DenseCloudData"
    dem_interpolation = "EnabledInterpolation"
    dem_resolution = 0

    ## Orthos settings
    ortho_surfacedata = "ElevationData"
    ortho_blending_mode = "MosaicBlending"
    ortho_fill_holes_bool = True
    ortho_ghosting_filter_bool = False
    ortho_cull_faces_bool = False
    ortho_refine_seamlines_bool = False
    ortho_resolution = 0

    ## Export settings
    export_bool = True
    export_formats = '[{"type": "mesh", "format": "obj", "settings": {"faces": 0, "texture": True}},{"type": "mesh", "format": "ply", "settings": {"faces": 500000, "texture": True}},{"type": "dem", "format": "tiff", "settings": {"resolution": 0}}]'
    short_coords = '[{"x": 0, "y": 0, "z": 0}]'

  ## Print settings
  print()
  print("Setting group: " + setting_group)
  print()
  print("Estimate image quality: " + str(est_iq_bool))
  print("Image quality threshold: " + str(iq_threshold))
  print()
  print("Align images: " + str(align_bool))
  print("Keypoint limit: " + str(keypoint_limit))
  print("Tiepoint limit: " + str(tiepoint_limit))
  print("Generic preselection: " + str(generic_preselection_bool))
  print("Reference preselection: " + str(reference_preselection_bool))
  print()
  print("Populate targets: " + str(poptargets_bool))
  print("CRS: EPSG::" + str(crs))
  print()  
  print("Uncheck markers: " + str(uncheckmarkers_bool))
  print("Add scalebars: " + str(scalebar_bool))
  print("Align bounding box: " + str(alignbbox_bool))
  print("Optimize alignment: " + str(optimizealignment_bool))
  print("Error reduction: " + str(err_red_bool))
  print("RU percent: " + str(RU_Percent))
  print("RU threshold: " + str(RU_Threshold))
  print("PA percent: " + str(PA_Percent))
  print("PA threshold: " + str(PA_Threshold))
  print("RE percent: " + str(RE_Percent))
  print("RE threshold: " + str(RE_Threshold))  
  print()
  print("Build depthmaps: " + str(depthmap_bool))
  print("Depth map quality: " + depthmap_quality)
  print("Depth map filter: " + depthmap_filter)
  print()  
  print("Build dense cloud: " + str(densecloud_bool))
  print()
  print("Build mesh: " + str(mesh_bool))
  print("Mesh surface type: " + str(surface_type))
  print("Mesh interpolation: " + str(interpolation))
  print("Mesh face count: " + str(face_count_custom))
  print("Mesh source data: " + str(source_data))
  print("Mesh vertex colours: " + str(vertex_colors_bool))
  print("Mesh vertex confidence: " + str(vertex_confidence_bool))
  print()
  print("Build texture: " + str(texture_bool))
  print("UV page count: " + str(uv_pages))
  print("Belnding mode: " + str(blending_mode))
  print("Texture size: " + str(texture_size))
  print("Texture type: " + str(texture_type))
  print("Enable ghosting filter: " + str(ghosting_filter_bool))
  print("Enable hole filling: " + str(fill_holes_bool))
  print()
  print("Build DEM: " + str(dem_bool))
  print("DEM datasource: " + str(dem_datasource))
  print("DEM interpolation: " + str(dem_interpolation))
  print("DEM resolution: " + str(dem_resolution))
  print()
  print("Build orthomosaic: " + str(ortho_bool))
  print("Surface data: " + str(ortho_surfacedata))
  print("Blending mode: " + str(ortho_blending_mode))
  print("Enable hole filling: " + str(ortho_fill_holes_bool))
  print("Enable ghosting filter: " + str(ortho_ghosting_filter_bool))
  print("Enable back-face culling: " + str(ortho_cull_faces_bool))
  print("Refine seamlines based on image content: " + str(ortho_refine_seamlines_bool))
  print("Ortho resolution: " + str(ortho_resolution))
  print()

def dbconnection(query, type):
  """ Connect to the PostgreSQL database server """
  connection = None
  try:
      # read connection parameters
      params = config()
      # connect to the PostgreSQL server
      print('Connecting to the PostgreSQL database...')
      connection = psycopg2.connect(**params)        
      # create a cursor
      cursor = connection.cursor()        
      # Execute query
      cursor.execute(query)
      if type == "insert":
        connection.commit()
        result = cursor.fetchall()
        count = cursor.rowcount
        print(count, "record(s) inserted.")
        if result:
          return result
      elif type == "update":
        connection.commit()
        result = cursor.fetchall()
        count = cursor.rowcount
        print(count, "record(s) updated.")
        if result:
          return result
      elif type == "select_one":
        result = cursor.fetchone()
        if result:
          print("One row returned.")
          return result
        else:
          print("No records found.")
      elif type == "select_all":
        result = cursor.fetchall()
        if result:
          return result
        else:
          print("No records found.")  
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)
  finally:
    if connection:
      cursor.close()
      connection.close()

#-----------------------------------------------------------------

def update_status(uuid, step, status):
  if mode == "db":
    query = (
    "UPDATE new.process_status "
    "SET " + step + " = '" + status + "' "
    "WHERE uuid = '" + uuid + "';"
    )
    dbconnection(query, "update")
    print("Updated " + step + " status to '" + status + "'. \n")

#-----------------------------------------------------------------

def update_processing(uuid, step, value):
  if mode == "db":
    query = (
    "UPDATE new.processing "
    "SET " + step + " = " + str(value) + " "
    "WHERE uuid = '" + uuid + "';"
    )
    dbconnection(query, "update")
#-----------------------------------------------------------------

def get_status(uuid, step):
  if mode == "db":
    query = (
    "SELECT " + step + " "
    "FROM new.process_status "
    "WHERE uuid = '" + uuid + "';"
    )
    status = dbconnection(query, "select_one")
    return status[0]

#-----------------------------------------------------------------

def set_software():
  if mode == "db":

    query = (
    "SELECT uuid "
    "FROM new.software "
    "WHERE software_name = 'Metashape' and software_version = '" + version + "';"
    )
    software_uuid = dbconnection(query, "select_one")

    if not software_uuid:
      query = (
        "INSERT INTO new.software (company, software_name, software_version, software_type) "
        "VALUES ('Agisoft'::varchar,'Metashape'::varchar,'" + version + "'::varchar, 'Photogrammetry'::varchar) "
        "RETURNING uuid"
        )
      software_uuid = dbconnection(query, "insert")
    return software_uuid[0]


#-----------------------------------------------------------------

def set_processing(uuid):
  if mode == "db":
    # Get uuid for current software version, if none, create the entry first:
    software_uuid = set_software()

    # Check if a processing entry linked to the capture and processing status entries exist
    query = (
    "SELECT proc.uuid "
    "FROM new.processing proc "
    "JOIN new.capture_processing_link cp ON cp.processing_uuid = proc.uuid "
    "JOIN new.capture cap ON cap.uuid = cp.capture_uuid "
    "JOIN new.process_status ps ON ps.capture_uuid = cap.uuid "
    "WHERE ps.uuid = '" + uuid + "'::uuid"
    )
    global processing_uuid
    try:
      processing_uuid = dbconnection(query, "select_one")[0]
    except Exception as e:
      # If the processing entry doesn't exist (if it's not linked, we assume it doesn't exist..), create it:
      query = (
        "INSERT INTO new.processing (software, processed_on) "
        "VALUES ( ARRAY ['" + software_uuid + "'::uuid], CURRENT_DATE) "
        "RETURNING uuid;"
        )
      # And link the newly created processing entry to the current capture entry via link-table.
      processing_uuid = dbconnection(query, "insert")[0][0]
      query = (
        "INSERT INTO new.capture_processing_link (capture_uuid, processing_uuid) "
        "SELECT cap.uuid, '" + processing_uuid + "'::uuid "
        "FROM new.capture cap "
        "JOIN new.process_status ps ON ps.capture_uuid = cap.uuid "
        "WHERE ps.uuid = '" + uuid + "';"
        )
      dbconnection(query, "insert")
    else:
      # If the processing entry already exists, update it with the current software info
      query = (
        "UPDATE new.processing "
        "SET software = (SELECT ARRAY_AGG(DISTINCT e) FROM UNNEST(software || '{" + software_uuid + "}') e) "
        "WHERE new.processing.uuid = '" + processing_uuid + "' ;"
        )
      dbconnection(query, "update")
    print()
    print("processing_uuid: " + str(processing_uuid))
    print("software_uuid: " + software_uuid)
    #return processing_uuid

#-----------------------------------------------------------------

def pickfoldernamechunk():
  # Create a new chunk named from a selected a folder and add all photos from that folder

  ## Select folder
  global path
  path = Metashape.app.getExistingDirectory("Select root folder for projects.")
  backslash = "/" # Metashape now uses slash (/) not backslash (\).
  print (path) # display full path and folder name in console
  bkslno = path.rfind(backslash)+1
  pathlen = len(path)
  folders = os.listdir(path)
  for folder in folders:
    folderpath = os.path.join(path,folder)
    if os.path.isdir(folderpath):
      print ('Create new chunk named "' + folder + '"')
      # create new chunk named after folder
      chunk = doc.addChunk()
      chunk.label = folder

      # load all images from specified folder into new chunk
      image_list = os.listdir(folderpath + "/Photos")
      photo_list = list()
      for photo in image_list:
        if ("jpg" or "jpeg" or "JPG" or "JPEG") in photo.lower():
          photo_list.append(folderpath + "/Photos/" + photo)
      chunk.addPhotos(photo_list)

  ## Remove empty chunks
  for chunk in list(doc.chunks):
    if not len(chunk.cameras):
      doc.remove(chunk)
  
  ## Save project
  camera = chunk.cameras[0]
  date = datetime.strptime(camera.photo.meta["Exif/DateTimeOriginal"], '%Y:%m:%d %H:%M:%S')
  #area = Metashape.app.getString(label = "Area mapped (for filename):", value = "Room")
  project_name = folder + "_" + date.strftime("%d%m%y") + ".psx"
  doc.save(path + "/" + project_name)
    
#-----------------------------------------------------------------

def loadfromdb():
  # Create a new chunk named from a selected a folder and add all photos from that folder
  query = "SELECT * FROM new.view_process_location"
  capture = dbconnection(query, "select_one")

  if not capture:
    sys.exit("No models to process. Exiting.")

  # Clear data from earlier runs
  doc.clear()

  # Select folder
  global path
  path = capture[1]
  global uuid
  uuid = capture[0]
  global folder
  folder = os.path.basename(path)
  backslash = "/" # Metashape now uses slash (/) not backslash (\).
  print (path) #display full path and folder name in console
  bkslno = path.rfind(backslash)+1
  pathlen = len(path)

  # Check for existing project and open
  existing_projects = glob.glob(path + '/' + folder + '_*.psx')
  if get_status(uuid, "status") not in ["done", "skip"]:
    if existing_projects:
      doc.open(existing_projects[0], read_only=False, ignore_lock=True)
      print("Project " + existing_projects[0] + " already exists. Opened existing project for editing.")
      update_status(uuid, "status", "processing")
      #return uuid
      return

  # Set status
  update_status(uuid, "status", "processing")

  #subfolders = os.listdir(path)
  #for subfolder in subfolders:
  if os.path.isdir(path):
    # Checking if chunk already exists.
    chunk_found = False
    for i in range(len(doc.chunks)):
      if str(doc.chunks[i].label) == str(folder):
        print("Chunk " + folder + " already exists.")
        doc.chunk = doc.chunks[i]
        chunk_found = True
        break
    # If chunk doesn't exist, create it.
    if not chunk_found:
      print ('Create new chunk named "' + folder + '"')
      #create new chunk named after folder
      chunk = doc.addChunk()
      chunk.label = folder
    #load all images from specified folder into new chunk
    image_list = os.listdir(path + "/Photos")
    photo_list = list()
    for photo in image_list:
      if ("jpg" or "jpeg" or "JPG" or "JPEG") in photo.lower():
        photo_list.append(path + "/Photos/" + photo)
    chunk.addPhotos(photo_list)

  #remove empty chunks
  for chunk in list(doc.chunks):
    if not len(chunk.cameras):
      doc.remove(chunk)
  
  #save project
  camera = doc.chunks[0].cameras[0]
  try:
    date = datetime.strptime(camera.photo.meta["Exif/DateTimeOriginal"], '%Y:%m:%d %H:%M:%S')
  except Exception as e:
    date = datetime.fromtimestamp(os.path.getmtime(photo_list[0]))
    
  #area = Metashape.app.getString(label = "Area mapped (for filename):", value = "Room")
  project_name = folder + "_" + date.strftime("%d%m%y") + ".psx"
  doc.save(path + "/" + project_name)
  return uuid
    
#-----------------------------------------------------------------

# Calculate image quality and disable images with quality less than a specified variable.
def estimagequality(threshold):

    # Calculate image quality and disable images with quality less than a specified variable.
  #chunk = doc.chunk
    
  #tlabel = 'Quality theshold'
  #threshold = Metashape.app.getFloat(tlabel, value=0.6) # photos with image quality below this amount will be disabled.
  #threshold = iq_threshold
  for chunk in doc.chunks:
    #camera = chunk.cameras
    #chunk.estimateImageQuality(camera)
    camerasniq = [camera for camera in chunk.cameras
      if 'Image/Quality' not in camera.meta]

    if len(camerasniq) > 0:
      #print('Test OK!')
      #print(found_major_version)
      if found_major_version == '1.5':
        chunk.estimateImageQuality(camerasniq)
      else:
        chunk.analyzePhotos(camerasniq)

    for i in range(0, len(chunk.cameras)):
      print('photo ' + str(i))
      camera = chunk.cameras[i]
      print(camera)
      quality = float(camera.meta['Image/Quality'])
      print(str(quality))
      if quality < threshold:
        camera.enabled = False
        print("Quality below threshold, camera disabled.")
    doc.save()
   
  mlabel = 'Photos with image quality less than ' + str(threshold) + ' disabled. Project saved.'
  #Metashape.app.messageBox(mlabel)     # display msgbox when done
  print(mlabel)
  
# -----------------------------------------------------------------------
def align():
  aligned_cameras = []
  for chunk in doc.chunks:
    chunk.detectMarkers()
    chunk.detectMarkers(inverted = True)
    chunk.matchPhotos(keypoint_limit = keypoint_limit, tiepoint_limit = tiepoint_limit, generic_preselection = generic_preselection_bool, reference_preselection = reference_preselection_bool)
    chunk.alignCameras()
    doc.save()
    for camera in chunk.cameras:
      if camera.transform!=None:
        aligned_cameras.append(camera)
  return len(aligned_cameras)
    
# -----------------------------------------------------------------------

def poptargets():

  targetfile = path + "/targets.csv"     # Path to the folder and target file name to write and read.

  # If target data in database, get targets and make csv
  if mode == "db":
    query = (
    "SELECT target_id, coord_x, coord_y, coord_z "
    "FROM new.view_gcp_targets "
    "WHERE status_uuid = '" + uuid + "';"
    )
    targets = dbconnection(query, "select_all")
    if len(targets)>0:
      with open(targetfile, "w") as f:
        csv_writer = csv.writer(f)
        for target_tuple in targets:
          csv_writer.writerow(target_tuple)
      print("Targets saved to " + targetfile)
    else:
      print("No targets in database, will check for local target.csv file.")

  target_list = []

  if os.path.exists(targetfile):
    for chunk in doc.chunks:
  
      chunk.crs = Metashape.CoordinateSystem("EPSG::" + str(crs))	
  
      #MarkersList = str(list(chunk.markers))                           # strings a list of class markers.
      #print (MarkersList)                                              # display list of detected targets in console.
  
      if found_major_version == '1.5':
        chunk.loadReference(targetfile, csvformat, columns='nxyz', delimiter=',', skip_rows=0) #import coord values.
      else:
        chunk.importReference(targetfile, csvformat, columns='nxyz', delimiter=',', skip_rows=0) #import coord values.
      chunk.updateTransform()
      doc.save()
  
      #List enabled targets
      for marker in chunk.markers:
        if marker.reference.enabled:
          target_list.append(marker)
  return len(target_list)

# -----------------------------------------------------------------------
def get_marker(chunk, label):
    for marker in chunk.markers:
        if marker.label == label:
             return marker
    return None

def add_scalebars():

  scalebarfile = path + "/scalebars.csv"     # Path to the folder and target file name to write and read.

  # If target data in database, get targets and make csv
  if mode == "db":
    query = (
    "SELECT target_first, target_second, distance, precision "
    "FROM new.view_scalebars "
    "WHERE status_uuid = '" + uuid + "';"
    )
    scalebars = dbconnection(query, "select_all")
    if len(scalebars)>0:
      with open(scalebarfile, "w") as f:
        csv_writer = csv.writer(f)
        for scalebar_tuple in scalebars:
          csv_writer.writerow(scalebar_tuple)
      print("Scalebars saved to " + scalebarfile)
    else:
      print("No scalebars in database, will check for local scalbars.csv file.")

  scalebar_list = []

  if os.path.exists(scalebarfile):
    for chunk in doc.chunks:
      print("Loading scalebars from " + scalebarfile)
      with open(scalebarfile, "r") as f:
        scalebars = csv.reader(f)
        scalebardict = dict()
        for i, scalebar_row in enumerate(scalebars):
          print("Row {}: {}".format(i, scalebar_row))
          if found_major_version == '1.5':
            first_marker = get_marker(chunk, scalebar_row[0])
            second_marker = get_marker(chunk, scalebar_row[1])
            print("First marker: {}".format(first_marker))
            print("Second marker: {}".format(second_marker))
            if first_marker and second_marker:
              print("Test OK, creating scalebar.")
              scalebardict['scalebar_%02d' % i] = chunk.addScalebar(first_marker, second_marker)
              scalebardict['scalebar_%02d' % i] .reference.distance = float(scalebar_row[2])
              scalebardict['scalebar_%02d' % i] .reference.accuracy = float(scalebar_row[3])
              scalebardict['scalebar_%02d' % i] .label = scalebar_row[0] + " - " + scalebar_row[1]
              print("Scalebar {} created.".format(scalebardict['scalebar_%02d' % i] .label))
          else:
            first_marker = get_marker(chunk, scalebar_row[0])
            second_marker = get_marker(chunk, scalebar_row[1])
            print("First marker: {}".format(first_marker))
            print("Second marker: {}".format(second_marker))
            if first_marker and second_marker:
              print("Test OK, creating scalebar.")
              scalebardict['scalebar_%02d' % i] = chunk.addScalebar(first_marker, second_marker)
              scalebardict['scalebar_%02d' % i] .reference.distance = float(scalebar_row[2])
              scalebardict['scalebar_%02d' % i] .reference.accuracy = float(scalebar_row[3])
              scalebardict['scalebar_%02d' % i] .label = scalebar_row[0] + " - " + scalebar_row[1]
              print("Scalebar {} created.".format(scalebardict['scalebar_%02d' % i] .label))
      chunk.updateTransform()
      doc.save()
  
      #List enabled targets
      for scalebar in chunk.scalebars:
        if scalebar.reference.enabled:
          scalebar_list.append(scalebar)
  return len(scalebar_list)  
#--------------------------------------------------------------------------------

#uncheckmarkers #unchecks markers in a chunk with two or fewer projections.
def uncheckmarkers():
  target_list = []
  #unchecks markers in a chunk with two or fewer projections.
  for chunk in doc.chunks:

    for i in range(0, len(chunk.markers)):
      marker = chunk.markers[i]
      print(marker)
      noproj = len(marker.projections)
      print(str(noproj))
      if noproj < 3:
        marker.reference.enabled = False
        print(str(marker) + " disabled.")
        
    doc.save()
    for marker in chunk.markers:
      if marker.reference.enabled:
        target_list.append(marker)

    print('All markers with fewer than 3 projections unchecked in chunk ' + chunk.label + '. Project saved.')
  return len(target_list)

# -----------------------------------------------------------------------

#calculate average total error in metres
def calc_error():
  error_list = []
  for chunk in doc.chunks:
    for marker in chunk.markers:
      try:
        source = chunk.crs.unproject(marker.reference.location) #measured values in geocentric coordinates
        estim = chunk.transform.matrix.mulp(marker.position) #estimated coordinates in geocentric coordinates
        local = chunk.crs.localframe(chunk.transform.matrix.mulp(marker.position)) #local LSE coordinates
        error = local.mulv(estim - source)
         
        total = error.norm()      #error points
        sum_squared = (total) ** 2    #Square root of error
        error_list += [sum_squared]      #List with errors
      except Exception as e:
        return 0

       
  error_sum = sum(error_list)
  n = len(error_list)
  if n > 0:
    ErrorTotal = (error_sum / n) ** 0.5
    return ErrorTotal
  else:
    return 0

# -----------------------------------------------------------------------
#alignbb2cs Aligns bounding boxes of all chunks to the grid
def alignbb2cs():

  for chunk in doc.chunks:
    T = chunk.transform.matrix
    v_t = T * Metashape.Vector( [0,0,0,1] )
    v_t.size = 3
    if chunk.crs:
      m = chunk.crs.localframe(v_t)
    else:
      m = Metashape.Matrix().diag([1,1,1,1])
    m = m * T
    s = math.sqrt(m[0,0] ** 2 + m[0,1] ** 2 + m[0,2] ** 2) #scale factor
    R = Metashape.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])
    R = R * (1. / s)
    reg = chunk.region
    reg.rot = R.t()
    chunk.region = reg
    doc.save()
  print("All bounding boxes aligned to grid. Project saved.")
    
#--------------------------------------------------------------------------------

#Optimize alignemnts
def optimizealignments():

  for chunk in doc.chunks:
    if found_major_version == '1.5': # Haven't cheked older versions, both the same for now
      chunk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=False, fit_b2=False, fit_k1=True, fit_k2=True, fit_k3=True, fit_k4=False, fit_p1=True, fit_p2=True, fit_corrections=False, adaptive_fitting=False, tiepoint_covariance=True)
    else:
      chunk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=False, fit_b2=False, fit_k1=True, fit_k2=True, fit_k3=True, fit_k4=False, fit_p1=True, fit_p2=True, fit_corrections=False, adaptive_fitting=False, tiepoint_covariance=True)
        
    doc.save()
    print('Camera positions optimised for chunk ' + chunk.label + '. Project saved.')
    
#--------------------------------------------------------------------------------
#Error reduction - Reconstruction Uncertainty
def reconstructionuncertainty():

  for chunk in doc.chunks:
    if found_major_version == '1.5': 
      continue
    else:
      points = chunk.point_cloud.points
      filter = Metashape.PointCloud.Filter()
      filter.init(chunk, criterion = Metashape.PointCloud.Filter.ReconstructionUncertainty) #Reconstruction Uncertainty
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
      print("Error Reduction Report for chunk " + chunk.label + ":")
      RU_actual_threshold = threshold
      print(str(threshold) + " threshold reached")
      print(str(StartPoints) + " points at start")
      print(str(target) + " points removed")
      print("Reconstruction Uncertainty filter completed")
    #doc.save()

#--------------------------------------------------------------------------------
#Error reduction - Projection Accuracy
def projectionaccuracy():

  for chunk in doc.chunks:
    if found_major_version == '1.5': 
      continue
    else:
      points = chunk.point_cloud.points
      filter = Metashape.PointCloud.Filter()
      filter.init(chunk, criterion = Metashape.PointCloud.Filter.ProjectionAccuracy) #Projection Accuracy
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
      print("Error Reduction Report for chunk " + chunk.label + ":")
      PA_actual_threshold = threshold
      print(str(threshold) + " threshold reached")
      print(str(StartPoints) + " points at start")
      print(str(target) + " points removed")
      print("Projection Accuracy filter completed")
    #doc.save()
    
#--------------------------------------------------------------------------------
#Error reduction - Reprojection Error
def reproductionerror():

  for chunk in doc.chunks:
    if found_major_version == '1.5': 
      continue
    else:
      points = chunk.point_cloud.points
      filter = Metashape.PointCloud.Filter()
      filter.init(chunk, criterion = Metashape.PointCloud.Filter.ReprojectionError) #Reprojection Error
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
      print("Error Reduction Report for chunk " + chunk.label + ":")
      RE_actual_threshold = threshold
      print(str(threshold) + " threshold reached")
      print(str(StartPoints) + " points at start")
      print(str(target) + " points removed")
      print("Reprojection Error filter completed")
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

def depthmaps():
  quality_map = {
    "Ultra": 1,
    "High": 2,
    "Medium": 4,
    "Low": 8,
    "Lowest": 16
  }
  #filter_attr = depthmap_filter + "Filtering"

  for chunk in doc.chunks:
    if found_major_version == '1.5':
      quality_attr = depthmap_quality + "Quality"
      chunk.buildDepthMaps(
        quality=quality_attr, 
        filter=depthmap_filter, 
        reuse_depth=True
        )
    else:
      quality_attr = quality_map[depthmap_quality]
      chunk.buildDepthMaps(
        downscale=quality_attr, 
        filter_mode=getattr(Metashape, depthmap_filter), 
        reuse_depth=True, max_neighbors=16, 
        subdivide_task=True, 
        workitem_size_cameras=20, 
        max_workgroup_size=100
        )
        
    doc.save()
    print('Depthmaps created for chunk ' + chunk.label + '. Project saved.')    

#--------------------------------------------------------------------------------
#
#Build Dense Cloud
def densecloud():
  for chunk in doc.chunks:
    if found_major_version == '1.5': # Haven't checked older versions, both the same for now
      chunk.buildDenseCloud()
    else:
      chunk.buildDenseCloud(
        point_colors=True, 
        point_confidence=False, 
        keep_depth=True, 
        max_neighbors=100,
        subdivide_task=True, 
        workitem_size_cameras=20, 
        max_workgroup_size=100
        )  
    doc.save()
    print('Dense cloud built for chunk ' + chunk.label + '. Project saved.')


#--------------------------------------------------------------------------------
#
#Build Mesh
def mesh():

  for chunk in doc.chunks:
    if found_major_version == '1.5': 
      chunk.buildModel(
        surface_type = getattr(Metashape, surface_type),
        interpolation = getattr(Metashape, interpolation),
        face_count = face_count_custom,
        source_data = getattr(Metashape, source_data),
        vertex_colors = vertex_colors_bool
        )
    else:
      chunk.buildModel(
        surface_type = getattr(Metashape, surface_type),
        interpolation = getattr(Metashape, interpolation),
        face_count_custom = face_count_custom,
        source_data = getattr(Metashape, source_data),
        vertex_colors = vertex_colors_bool,
        vertex_confidence = vertex_confidence_bool
        )
    doc.save()
    print('Mesh built for chunk ' + chunk.label + '. Project saved.')


#--------------------------------------------------------------------------------
#
#Build UV Maps and Texture
def texture(divider = 1):

  for chunk in doc.chunks:
    if found_major_version == '1.5': # Haven't cheked older versions, both the same for now
      chunk.buildUV(page_count = uv_pages, texture_size = texture_size)
      chunk.buildTexture(texture_size = texture_size, ghosting_filter = ghosting_filter_bool)
    else:
      chunk.buildUV(
        mapping_mode = Metashape.GenericMapping,
        page_count = uv_pages, 
        texture_size = texture_size / divider)
      chunk.buildTexture(
        blending_mode = getattr(Metashape, blending_mode),
        texture_size = texture_size / divider,
        fill_holes = fill_holes_bool,
        ghosting_filter = ghosting_filter_bool,
        texture_type = getattr(Metashape.Model.TextureType, texture_type)
        )
    doc.save()
    print('UV maps and texture created for chunk ' + chunk.label + '. Project saved.')

#--------------------------------------------------------------------------------
#
#Build DEM
def dem():

  for chunk in doc.chunks:
    if found_major_version == '1.5':
      chunk.buildDem(
        source = getattr(Metashape, dem_datasource), 
        interpolation = getattr(Metashape, dem_interpolation)
        )
    else:
      # print(str(dem_params))
      # chunk.buildDem(**dem_params)
      chunk.buildDem(
        source_data = getattr(Metashape, dem_datasource), 
        interpolation = getattr(Metashape, dem_interpolation),  
        resolution = dem_resolution, 
        subdivide_task = True
        )


    doc.save()
    print('DEM created for chunk ' + chunk.label + '. Project saved.')

#--------------------------------------------------------------------------------
#
#Build Orthomosaic
def ortho():

  for chunk in doc.chunks:
    if found_major_version == '1.5':
      chunk.buildOrthomosaic(
        surface=getattr(Metashape, ortho_surfacedata), 
        blending=getattr(Metashape, ortho_blending_mode), 
        fill_holes=ortho_fill_holes_bool,
        cull_faces=ortho_cull_faces_bool,
        refine_seamlines=ortho_refine_seamlines_bool
        )
    else:
      chunk.buildOrthomosaic(
        surface_data = getattr(Metashape, ortho_surfacedata),
        blending_mode = getattr(Metashape, ortho_blending_mode),
        fill_holes = ortho_fill_holes_bool,
        ghosting_filter = ortho_ghosting_filter_bool,
        cull_faces = ortho_cull_faces_bool,
        refine_seamlines = ortho_refine_seamlines_bool,
        resolution = ortho_resolution
        )

    doc.save()
    print('Orthomosaic created for chunk ' + chunk.label + '. Project saved.')

#--------------------------------------------------------------------------------
#
#Export data
def export():
  output_folder = path + '/exports/'
  if not os.path.exists(output_folder):
    os.mkdir(output_folder)

  description_text = (
    'The project contains objects NN from NN, \n captured by NN on the DD.MM.YYYY \n ' 
    'using X equipment. The resulting exports are licensed  XY by KHM/NN.'
    )
  settings = [('Test 1', 'Value 1'), ('Test 2', 'Value 2')]

  faceCount = 500000  #Number of faces for decimated mesh

  # Check and set shorhtened coordinates
  if short_coords:
    print("Shortcoords: " + str(short_coords))
    short_coord_file = path + "/short_coords.csv"     # Path to the folder and target file name to write and read.
    #short_coord_dict = json.loads(short_coords)

  # Write short coords to csv in project folder
    with open(short_coord_file, "w") as f:
      csv_writer = csv.DictWriter(f, short_coords.keys())
      csv_writer.writeheader()
      csv_writer.writerow(short_coords)
    print("Shorthened coordinate data saved to " + short_coord_file)

  # Apply to ply export (with decimated mesh?) for use by meshlab and 3dhop
    shiftCoords =  Metashape.Vector( (short_coords['x'], short_coords['y'], short_coords['z']) )
  else:
    shiftCoords =  Metashape.Vector( 0, 0, 0)

  # Def formats
  ply = Metashape.ModelFormatPLY
  obj = Metashape.ModelFormatOBJ
  laz = Metashape.PointsFormatLAZ
  comment = "KHM " + str(date.today().year)

  for chunk in doc.chunks:
    crs = chunk.crs

    if found_major_version == '1.5':
      print("Version 1.5 export not yet set.")
      if chunk.point_cloud:
        filename_densepoint = output_folder + 'pointcloud_' + processing_uuid + '.las'
        chunk.exportPointCloud(
          filename_densepoint, 
          source_data = Metashape.PointCloudData
          )      
    else:
      filename_report = output_folder + 'report_' + processing_uuid + '.pdf'
      chunk.exportReport(
        path = filename_report,  
        title = folder, 
        description = processing_uuid
        #user_settings = settings
        )
      print("Report exported as " + filename_report)

      if chunk.model:
        filename_model = output_folder + 'model_' + processing_uuid + '.obj'
        chunk.exportModel(
          filename_model,
          binary = False,  
          clip_to_boundary=False, 
          precision=6, 
          save_texture=True, 
          embed_texture=True, 
          save_normals=True, 
          save_colors=True, 
          save_cameras=True, 
          strip_extensions=False, 
          format = obj, 
          crs = crs, 
          comment = comment, 
          save_comment = True
          )
        print()
        print("Model exported as " + filename_model)
        duplicateMesh = Metashape.Tasks.DuplicateAsset()
        duplicateMesh.asset_type = Metashape.ModelData
        duplicateMesh.clip_to_boundary = False
        duplicateMesh.asset_key = chunk.models[0].key
        duplicateMesh.apply(chunk)
        chunk.decimateModel(face_count=faceCount, apply_to_selection=False)
        chunk.buildUV(mapping_mode=Metashape.GenericMapping, texture_size=4096)
        chunk.buildTexture(blending_mode=Metashape.MosaicBlending, texture_size=4096, fill_holes=True, ghosting_filter=True)
        decimated_model = output_folder + 'model_shortcoords_' + processing_uuid
        filename_decimated_model = decimated_model + '.ply'
        chunk.exportModel(
          filename_decimated_model, 
          binary=True, 
          clip_to_boundary=False,  
          save_texture=True, 
          embed_texture=True, 
          save_normals=True, 
          save_colors=True, 
          save_cameras=True, 
          strip_extensions=False, 
          format=ply, 
          crs=crs, 
          shift=shiftCoords
          )
        print()
        print("Decimated model with shortened coordinates exported as " + filename_decimated_model)

      if chunk.point_cloud:
        filename_densepoint = output_folder + 'pointcloud_' + processing_uuid + '.las'
        chunk.exportPoints(
          filename_densepoint, 
          source_data = Metashape.DenseCloudData,
          save_normals=True,
          save_colors=True,
          save_confidence=True,
          format= laz,
          crs = crs,
          comment = comment
          )

      if chunk.elevation:
        filename_dem = output_folder + 'dem_' + processing_uuid + '.tif'
        chunk.exportRaster(
          filename_dem, 
          source_data = Metashape.ElevationData
          )

      if chunk.orthomosaic:
        filename_ortho = output_folder + 'ortho_' + processing_uuid + '.tif'
        chunk.exportRaster(
          filename_ortho, 
          source_data = Metashape.OrthomosaicData
          )

    doc.save()
    print('Orthomosaic created for chunk ' + chunk.label + '. Project saved.')

  # Create Nexus files

  # Prepare mesh in MeshLab
  extless_filename_model = os.path.splitext(filename_model)[0]
  ms = pymeshlab.MeshSet()
  ms.load_new_mesh(filename_model)
  ms.save_current_mesh(
    extless_filename_model + ".ply", 
    binary=True, 
    save_vertex_normal=False, 
    save_face_color=False,
    save_wedge_texcoord=True
    )

  os.environ['PATH'] += ':'+'/home/hallvard/Apps/nexus/nexus/bin'
  try:
    build_nxs = "nxsbuild " + extless_filename_model + ".ply -o " + extless_filename_model + ".nxs"
    subprocess.run(build_nxs, shell=True)
  except Exception as e:
    build_nxs = "nxsbuild -G" + extless_filename_model + ".ply -o " + extless_filename_model + ".nxs"
    subprocess.run(build_nxs, shell=True)
  finally:
    build_nxz = "nxsedit -z " + extless_filename_model + ".nxs -o " + extless_filename_model + ".nxz"
    subprocess.run(build_nxz, shell=True)
  
  


#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#  Run script #-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

def run(runmode):
  
  global mode
  mode = runmode

  # Check mode, and create project
  if mode == "standalone":
    print("Mode: Manual, standalone.")
    pickfoldernamechunk()
    global uuid
    uuid = ""
  elif mode == "db":
    print("Mode: PostgreSQL database.")
    loadfromdb()
    set_processing(uuid)  
  # Get/set variables
  vars(uuid)
  
  # Estimate image quality
  if est_iq_bool:
    print("")
    print("***** Estimating Image Quality *****")
    print("")
    if get_status(uuid, "estimating_iq") in ["done", "skip"]:
      print("Image quality estimation already done. Skipping.\n")
    else:
      update_status(uuid, "estimating_iq", "processing")
      try:
        estimagequality(iq_threshold)
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "estimating_iq", "failed")
      else:
        update_status(uuid, "estimating_iq", "done")
  
  # Align images  
  if align_bool:
    print("")
    print("***** Aligning Images *****")
    print("")
    if get_status(uuid, "aligning") in ["done", "skip"]:
      print("Image aligning already done. Skipping.\n")
    else:
      update_status(uuid, "aligning", "processing")
      try:
        images_aligned = align()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "aligning", "failed")
      else:
        update_processing(processing_uuid, "images_aligned", images_aligned)
        update_status(uuid, "aligning", "done")
  
  
  # Populate targets
  if poptargets_bool:
    print("")
    print("***** Georeferencing Targets *****")
    print("")    
    if get_status(uuid, "populating_targets") in ["done", "skip"]:
      print("Target population already done. Skipping.\n")
    else:
      update_status(uuid, "populating_targets", "processing")
      try:
        targets_used = poptargets()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "populating_targets", "failed")
      else:
        update_processing(processing_uuid, "targets_used", targets_used)
        error = calc_error()
        update_processing(processing_uuid, "estimated_error", error)
        update_status(uuid, "populating_targets", "done")

  # Uncheck markers with less than N projections
  if uncheckmarkers_bool:
    print("")
    print("***** Unchecking Markers *****")
    print("")    
    if get_status(uuid, "uncheckingmarkers") in ["done", "skip"]:
      print("Target population already done. Skipping.\n")
    else:
      update_status(uuid, "uncheckingmarkers", "processing")
      try:
        targets_used = uncheckmarkers()
        error = calc_error()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "uncheckingmarkers", "failed")
      else:
        print(str(targets_used) + " targets used.") 
        update_processing(processing_uuid, "targets_used", targets_used)
        update_processing(processing_uuid, "estimated_error", error)
        update_status(uuid, "uncheckingmarkers", "done")

  # Populate Scalebars
  if scalebar_bool:
    print("")
    print("***** Adding Scalebars *****")
    print("")    
    if get_status(uuid, "adding_scalebars") in ["done", "skip"]:
      print("Scalebars alrady added. Skipping.\n")
    else:
      update_status(uuid, "adding_scalebars", "processing")
      try:
        scalebars_used = add_scalebars()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "adding_scalebars", "failed")
      else:
        print(str(scalebars_used) + " scalebars used.")
        update_processing(processing_uuid, "scalebars_used", scalebars_used)
        update_status(uuid, "adding_scalebars", "done")        
  
  # Align Bounding boxes to grid
  if alignbbox_bool:
    print("")
    print("***** Aligning Bounding Box *****")
    print("")    
    if get_status(uuid, "aligning_bbox") in ["done", "skip"]:
      print("Bounding boxes already aligned to grid. Skipping.\n")
    else:
      update_status(uuid, "aligning_bbox", "processing")
      try:
        alignbb2cs()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "aligning_bbox", "failed")
      else:
        update_status(uuid, "aligning_bbox", "done")
  
  # Optimise alignment (first time)
  if optimizealignment_bool:
    print("")
    print("***** Optimising Alignment *****")
    print("")    
    if get_status(uuid, "optimizing_alignment") in ["done", "skip"]:
      print("Alignment already optimised. Skipping.\n")
    else:
      update_status(uuid, "optimizing_alignment", "processing")
      try:
        optimizealignments()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "optimizing_alignment", "failed")
      else:
        error = calc_error()
        update_processing(processing_uuid, "estimated_error", error)
        update_status(uuid, "optimizing_alignment", "done")
      
  # Reducing errors and re-optimising alignment
  if err_red_bool:
    print("")
    print("***** Running Error Reduction Algorithms *****")
    print("")    
    if get_status(uuid, "reducing_error") in ["done", "skip"]:
      print("Error reduction already done. Skipping.\n")
    else:
      update_status(uuid, "reducing_error", "processing")
      try:
        reconstructionuncertainty()
        optimizealignments()
        projectionaccuracy()
        optimizealignments()
        reproductionerror()
        optimizealignments()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "reducing_error", "failed")
      else:
        error = calc_error()
        update_processing(processing_uuid, "estimated_error", error)
        update_status(uuid, "reducing_error", "done")
  
  # Build Depth Maps
  if depthmap_bool:
    print("")
    print("***** Building Depthmaps *****")
    print("")    
    if get_status(uuid, "building_depthmaps") in ["done", "skip"]:
      print("Depthmaps already built. Skipping.\n")
    else:
      update_status(uuid, "building_depthmaps", "processing")
      try:
        depthmaps()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "building_depthmaps", "failed")
      else:
        update_processing(processing_uuid, "depth_maps_created", "true")
        update_status(uuid, "building_depthmaps", "done")
  
  # Build Dense Cloud
  if densecloud_bool:
    print("")
    print("***** Building Dense Cloud *****")
    print("")    
    if get_status(uuid, "building_densecloud") in ["done", "skip"]:
      print("Dense cloud already built. Skipping.\n")
    else:
      update_status(uuid, "building_densecloud", "processing")
      try:
        densecloud()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "building_densecloud", "failed")
      else:
        update_processing(processing_uuid, "dense_point_cloud_created", "true")
        update_status(uuid, "building_densecloud", "done")
  
  # Build Mesh
  if mesh_bool:
    print("")
    print("***** Creating Mesh *****")
    print("")    
    if get_status(uuid, "meshing") in ["done", "skip"]:
      print("Mesh already built. Skipping.\n")
    else:
      update_status(uuid, "meshing", "processing")
      try:
        mesh()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "meshing", "failed")
      else:
        update_processing(processing_uuid, "mesh_created", "true")
        update_status(uuid, "meshing", "done")
  
  # Build Texture
  if texture_bool:
    print("")
    print("***** Creating Texture *****")
    print("")    
    if get_status(uuid, "texturing") in ["done", "skip"]:
      print("Mesh already built. Skipping.\n")
    else:
      update_status(uuid, "texturing", "processing")
      try:
        texture()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "texturing", "failed")
      else:
        update_processing(processing_uuid, "texture_created", "true")
        update_status(uuid, "texturing", "done")
  
  # DEM
  if dem_bool:
    print("")
    print("***** Building DEM *****")
    print("")    
    if get_status(uuid, "building_dem") in ["done", "skip"]:
      print("DEM already made. Skipping.\n")
    else:
      update_status(uuid, "building_dem", "processing")
      try:
        dem()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "building_dem", "failed")
      else:
        update_processing(processing_uuid, "dem_created", "true")
        update_status(uuid, "building_dem", "done")
  
  # Orthophoto
  if ortho_bool:
    print("")
    print("***** Building Orthomosaic *****")
    print("")    
    if get_status(uuid, "building_ortho") in ["done", "skip"]:
      print("Orthomosaic already made. Skipping.\n")
    else:
      update_status(uuid, "building_ortho", "processing")
      try:
        ortho()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "building_ortho", "failed")
      else:      
        update_processing(processing_uuid, "orthophoto_created", "true")
        update_status(uuid, "building_ortho", "done")      
  
  # Decimate mesh
  
  
  
  # Exports
  if export_bool:
    print("")
    print("***** Exporting results *****")
    print("")    
    if get_status(uuid, "exporting") in ["done", "skip"]:
      print("Exports already done. Skipping.\n")
    else:
      update_status(uuid, "exporting", "processing")
      try:
        export()
      except Exception as e:
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        update_status(uuid, "exporting", "failed")
      else:
        update_status(uuid, "exporting", "done")
      
  return uuid



# Run the script if this is main
if __name__ == "__main__":
  # Set command line arguments
  argParser = argparse.ArgumentParser()
  argParser.add_argument("-m", "--mode", nargs='?', const="db", type=str, default="db", help="Script mode, 'db' or 'standalone'.")
  args = argParser.parse_args()
  mode = args.mode
  # Run
  try:
    run(mode)
  except Exception as e:
    # Set status failed
    print()
    print("!!!!! Exception !!!!!")
    print(e)
    print()
    update_status(uuid, "status", "failed")
  else:
    # Set status done
    update_status(uuid, "status", "done")