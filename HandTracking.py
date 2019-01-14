from freenect import sync_get_depth as get_depth # Uses freenect to get depth information from the Kinect
import numpy as np  # Imports NumPy
import cv2  # Uses both of cv and cv2
import pygame  # Uses pygame

from random import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from functools import partial
from kivy.graphics import Color, PushMatrix, PopMatrix, Rotate, Translate
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout

from kivy.graphics.texture import Texture
# The libaries below are used for mouse manipulation
from Xlib import X, display
import Xlib.XK
import Xlib.error
import Xlib.ext.xtest

from kivy.graphics import ( Translate, Fbo, ClearColor, ClearBuffers, Scale)

import apiFaceAndEmotion

from functools import partial

#http://opencvpython.blogspot.pt/2012/04/contour-features.html
#http://www.mathworks.com/help/images/ref/regionprops.html
# http://code.activestate.com/recipes/578104-openkinect-mouse-control-using-python/?in=user-4179768

constList = lambda length, val: [val for _ in range(length)]  # Gives a list of size length filled with the variable val. length is a list and val is dynamic

"""
This class is a less extensive form of regionprops() developed by MATLAB. It finds properties of contours and sets them to fields
"""

class BlobAnalysis:
    def __init__(self, BW):  # Constructor. BW is a binary image in the form of a numpy array
        self.BW = BW

        _, cnts, hierarchy = cv2.findContours(self.BW.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)# Finds the contours
        counter = 0
        """
        These are dynamic lists used to store variables
        """
        centroid = list()
        contourArea = list()

        for cnt in cnts:  # Iterate through the CvSeq, cs.
            area = cv2.contourArea(cnt)
            if abs(area) > 2000:  # Filters out contours smaller than 2000 pixels in area
                contourArea.append(area)  # Appends contourArea with newest contour area
                m = cv2.moments(cnt)  # Finds all of the moments of the filtered contour
                if m['m00'] != 0.0:
                    cx = m['m10'] / m['m00']
                    cy = m['m01'] / m['m00']
                    centroid.append((int(cx), int(cy)))
                    counter += 1  # Adds to the counter to see how many blobs are there
        """
        Below the variables are made into fields for referencing later
        """
        self.centroid = centroid
        self.counter = counter


class MyHandTrackingApp(Widget):

    def __init__(self,**kwargs):
        super(MyHandTrackingApp, self).__init__(**kwargs)
        self.painter = Widget()
        self.painter.width = 640
        self.painter.height = 480
        self.init_stuff()
        Clock.schedule_interval(partial(self.actualise_camera), 0)

    def init_stuff(self):
        self.parent= App.get_running_app()
        #todo: use config file distances
        self.distance_hand_is_close=600 #default 600 , I think min is 500
        self.distance_background=700 #default 900

        self.sensitivity_x=2#default 2
        self.sensitivity_y=2#default 2

        self.centroidList = list()  # Initiate centroid list
        # RGB Color tuples
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.PURPLE = (255, 0, 255)
        self.BLUE = (0, 0, 255)
        self.WHITE = (255, 255, 255)
        self.YELLOW = (255, 255, 0)
        self.dummy = False  # Very important bool for mouse manipulation
        self.d = display.Display()  # Display reference for Xlib manipulation
        self.time=0

    def move_mouse(self, x, y):  # Moves the mouse to (x,y). x and y are ints
        s = self.d.screen()
        root = s.root
        root.warp_pointer(x, y)
        self.d.sync()

    def click_down(self, button):  # Simulates a down click. Button is an int
        print("click")
        Xlib.ext.xtest.fake_input(self.d, X.ButtonPress, button)
        self.d.sync()

    def click_up(self, button):  # Simulates a up click. Button is an int
        Xlib.ext.xtest.fake_input(self.d, X.ButtonRelease, button)
        self.d.sync()

    """
    The function below is a basic mean filter. It appends a cache list and takes the mean of it.
    It is useful for filtering noisy data
    cache is a list of floats or ints and val is either a float or an int
    it returns the filtered mean
    """

    def cacheAppendMean(self, cache, val):
        cache.append(val)
        del cache[0]
        return np.mean(cache)

    """
    This is the GUI that displays the thresholded image with the convex hull and centroids. It uses pygame.
    Mouse control is also dictated in this function because the mouse commands are updated as the frame is updated
    """

    def actualise_camera(self, dt):
        self.painter.canvas.after.clear()
        self.painter.canvas.before.clear()

        (depth, _) = get_depth()  # Get the depth from the kinect
        depth = depth.astype(np.float32)  # Convert the depth to a 32 bit float
        _, depthThresh = cv2.threshold(depth, self.distance_hand_is_close, 255,
                                       cv2.THRESH_BINARY_INV)  # Threshold the depth for a binary image. Thresholded at 600 arbitary units
        _, back = cv2.threshold(depth, self.distance_background, 255,
                                cv2.THRESH_BINARY_INV)  # Threshold the background in order to have an outlined background and segmented foreground
        _,wayBack = cv2.threshold(depth, 2000, 255, cv2.THRESH_BINARY_INV)
        blobData = BlobAnalysis(depthThresh)  # Creates blobData object using BlobAnalysis class
        blobDataBack = BlobAnalysis(back)  # Creates blobDataBack object using BlobAnalysis class
        blobDataWayBack = BlobAnalysis(wayBack)

        if(blobDataWayBack.counter != 0 and blobDataBack.counter==0):
            if(self.time==0):
                self.parent.check_users()
                self.time=100
            else:
                self.time-=1
        else:
            self.time=0
        if(blobDataBack.counter==0):#not interractive
            self.parent.hide_overlay()
            for i in range(blobData.counter):  # Iterate from 0 to the number of blobs minus 1
                self.centroidList.append(blobData.centroid[i])  # Adds the centroid tuple to the centroidList --> used for drawing
        else:
            self.parent.show_overlay()
            # draw contours
            with self.painter.canvas.before:
                PushMatrix()
                Rotate(angle=180, axis=(0, 0, 1), origin=self.painter.center)
                Translate(self.painter.width / 2 - 320, self.painter.height / 2 - 240)

                for i in range(blobData.counter):  # Iterate from 0 to the number of blobs minus 1
                    self.centroidList.append( blobData.centroid[i])  # Adds the centroid tuple to the centroidList --> used for drawing
                    Color(self.RED[0], self.RED[1], self.RED[2], mode='rgb')
                    Line(circle=(blobData.centroid[i][0], blobData.centroid[i][1], 20))

            with self.painter.canvas.after:
                PopMatrix()

        del depth  # Deletes depth --> opencv memory issue

        # Mouse Try statement
        try:
            centroidX = blobData.centroid[0][0]
            centroidY = blobData.centroid[0][1]
            if self.dummy:
                mousePtr = display.Display().screen().root.query_pointer()._data  # Gets current mouse attributes
                dX = centroidX - self.strX  # Finds the change in X
                dY = self.strY - centroidY  # Finds the change in Y
                if abs(dX) > 1:  # If there was a change in X greater than 1...
                    mouseX = mousePtr["root_x"] - self.sensitivity_x * dX  # New X coordinate of mouse
                if abs(dY) > 1:  # If there was a change in Y greater than 1...
                    mouseY = mousePtr["root_y"] - self.sensitivity_y * dY  # New Y coordinate of mouse
                self.move_mouse(mouseX, mouseY)  # Moves mouse to new location
                self.strX = centroidX  # Makes the new starting X of mouse to current X of newest centroid
                self.strY = centroidY  # Makes the new starting Y of mouse to current Y of newest centroid

            else:
                self.strX = centroidX  # Initializes the starting X
                self.strY = centroidY  # Initializes the starting Y
                self.dummy = True  # Lets the function continue to the first part of the if statement
        except:  # There may be no centroids and therefore blobData.centroid[0] will be out of range
            self.dummy = False  # Waits for a new starting point
