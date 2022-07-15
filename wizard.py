#!usr/bin/env python
import os
import sys
import shutil
from config_gen import *
from model_gen import *
from world_gen import *
from subprocess import call
import time
import cv2
from urllib.request import urlretrieve
import math
import numpy as np 

class worldSettings(object):
    def __init__(self):
        self.ambient = "120 120 120 255"
        self.time = "10:00"

    def worldScene(self):
        self.time = input("Enter time of day[24 hrs](hh:mm): ")
        time = self.time[0:2]
        time = int(time)

        #Night / Early Morning
        if time<6 or time>=21:
            self.ambient = "20 40 50 255"
        #Dawn
        elif time<7 and time>=6:
            self.ambient = "120 80 60 255"
        #After Dawn
        elif time<8 and time>=7:
            self.ambient = "120 70 80 255"
        #Before Dusk
        elif time<20 and time>19:
            self.ambient = "120 70 80 255"
        #Dusk
        elif time<21 and time>=20:
            self.ambient = "120 80 60 255"


def modelFolderGenerator(heightmap):

    #Creating our auto generated terrain model directory
    os.chdir(os.path.expanduser("~/.gazebo/models/"))
    path = os.getcwd()
    items = os.listdir(path)

    for item in items:
        if "autogen_terrain" == item:
            shutil.rmtree("autogen_terrain")

    os.mkdir("autogen_terrain")

    #Changing the current working directory
    os.chdir("autogen_terrain")

    #Creating the model.config file
    configGenerator()

    #Creatinf the model.sdf file
    modelGenerator()

    #Creating the model materials folder
    os.mkdir("materials")
    os.chdir("materials")
    os.mkdir("textures")
    os.chdir("textures")

    #Saving the heightmap inside terrain model textures
    cv2.imwrite("heightmap.png",heightmap)


def imageResizer(path):


    # print("___imageResizer___ extracting data from : ", path)

    if path.find('.hgt') != -1:

    
        #### B_option 1: retrieve .hgt as data array, works pretty fine
        # siz = os.path.getsize(path)
        # dim = int(math.sqrt(siz/2))
    
        # assert dim*dim*2 == siz, 'Invalid file size'
    
        # data = np.fromfile(path, np.dtype('>i2'), dim*dim).reshape((dim, dim))
        
        ## B_resize to desired size
        #### B_todo: try original size by getting geolocation and size of the image
        
        # hm_resize = cv2.resize(data,(129,129))

        #### B_option 2: open with gdal and retrieve geoinfo 
        from osgeo import gdal
        dataset = gdal.Open(path, gdal.GA_ReadOnly)

        ## print dataset info:
        print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
                                dataset.GetDriver().LongName))
        print("Size is {} x {} x {}".format(dataset.RasterXSize,
                                        dataset.RasterYSize,
                                        dataset.RasterCount))
        print("Projection is {}".format(dataset.GetProjection()))
        geotransform = dataset.GetGeoTransform()
        if geotransform:
           print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
           print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))
          
            
        band = dataset.GetRasterBand(1)
        print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))
        
        min = band.GetMinimum()
        max = band.GetMaximum()
        if not min or not max:
            (min,max) = band.ComputeRasterMinMax(True)
        print("Min Elevation ={:.3f}, Max Elevation ={:.3f}".format(min,max))
        
        ## below requires string data to be reparsed..            
        # dataset_info = gdal.Info(path)
        
        aaba = 1 

    
    elif path.find('-') != -1:
        path = path[:-1]
        print("___imageResizer___ extracting data from : ", path)

    else:   
        hm = cv2.imread(path)
        resize_im = 257
        # return error if hm is None
        hm_resize = cv2.resize(hm,(129,129))

    return hm_resize



if __name__ == "__main__":

    #Welcome text
    cwd = os.getcwd()
    print(cwd)
    print("WELCOME TO AUTOMATIC TERRAIN GENEREATOR")

    #Choice Menu
    check = False
    while check == False:
        #### ui inputs
        print("1. Insert Heightmap from disk")
        print("2. Insert Heightmap from URL")
        print("3. Use Earth's Terrain")

        choice = int(input("Enter a choice: "))

        #Heightmap on Disk
        if choice == 1:
            path = input("Enter the location of the heightmap:")
            filename = input("Enter tile name, skip with '-'")
            check = True

        #Heightmap from URL
        elif choice == 2:
            link = input("Enter the url of heightmap:")
            urlretrieve(link,"img.png")
            path = "./img.png"
            check = True

        #HeightMap of Earth's terrain
        elif choice == 3:
            prin("\nUnder Development, choose something else!\n")
            check = False

        #Default Case
        else:
            print("\nPlase enter a valid choice.!\n")
            check = False

    '''
    #Ask user for heightmap input
    check = input("Do you have a heightmap?(y/n):")

    #Take in heightmap as a url or as file on disk
    if check=="y" or check=="Y":
        path = input("Enter the location of the heightmap:")
    else:
        link = input("Enter the url of heightmap:")
        urlretrieve(link,"img.png")
        path = "./img.png"
    '''
    
    #### B_todo: get & set more options, including, bbox, pixel_resize, etc.
    #Resizing the image to 2*n+1 dimention: (129x129)
    
    ## B retrieve path from filename if given
    if filename is not None or filename !='-' or filename !='abort' :
        path = path + filename
        print("loading heightmap")

    heightmap = imageResizer(path)

    #Creating a autogen_terrain folder with terrain information and also the world file
    modelFolderGenerator(heightmap)

    #Saving Textures into the terrain model
    os.chdir(os.path.expanduser(cwd))
    os.chdir("textures")
    texture_path = os.getcwd()
    imgfiles = os.listdir(texture_path)
    for imgfile in imgfiles:
        command = "cp "+str(imgfile)+" ~/.gazebo/models/autogen_terrain/materials/textures/"
        os.system(command)

    #Changing the directory to the output path for the .world
    destination = input("World file destination(Press Enter to pass):")
    if destination=="":
        destination=cwd
    os.chdir(destination)


    #Creating our world file
    w = worldSettings()
    w.worldScene()
    worldGenerator(w)


    #Success output
    print("Terrain successully generated")

    #Opening the generated world in Gazebo
    time.sleep(1)
    print("Loading World...")

    call(["gazebo","terrain.world"])

    os.chdir(os.path.expanduser(cwd))
