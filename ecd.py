# -*- coding: utf-8 -*-
"""
Created on Sun Dec  6 11:18:58 2020

@author: Nick Brusco

ECD = Early Collision Debugger. 
This script is to aid in finding and eliminating the bug where drifter shows a collision
far before it hits a wall
"""
import TrackGen
from NEAT_drifter_class import Drifter
import Box2D  # The main library
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, vec2, chainShape, rayCastCallback)
from Box2D.examples.raycast import RayCastClosestCallback, b2RayCastCallback
import pygame
from pygame.locals import *
from pygame.color import THECOLORS
import pymunk.pygame_util
import numpy as np
import random

PPM = 10.0
SCREEN_WIDTH, SCREEN_HEIGHT = 1300, 700

def tfm(meters):
    '''transforms from meters to pixels for single values and points'''
    if type(meters) == int:
        return meters*PPM
    elif type(meters) == list:
        rv = []
        for item in meters:
            if type(item) in [list,tuple]: #handle lists of lists of points
                rv.append([item[0]*PPM,item[1]*PPM])
            else:
                rv.append(item*PPM)
        return rv
    else:
        return None
    
def rtfm(pix):
    '''reverse transforms a list of points from pixels to meters'''
    rv = []
    if type(pix[0]) in[int]:
        return [pix[0]/PPM, pix[1]/PPM]
    
    for point in pix:
        rv.append([(point[0]/PPM),(point[1]/PPM)])
    return rv

dft = Drifter() #should only be used to help TG render
tg = TrackGen.TrackGen(dft)

rv = None
while(rv == None):
    rv = tg.step()
centerline, left, right, checkpoints = (rv)
    

#setup world
# --- pybox2d world setup ---
world = world(gravity=(0, 0), doSleep=True)
bodies = []
tracks = []

#track setup
outer_track = world.CreateBody(shapes=chainShape(vertices=rtfm(left)))
inner_track = world.CreateBody(shapes=chainShape(vertices=rtfm(right)))
centerline = centerline
#fix cw/ccw
outer_track.fixtures[0].userData = 'outer'
callback = RayCastClosestCallback()
i=0
while callback.hit == False:  
    world.RayCast(callback, (i-10,-10), (i-10,SCREEN_HEIGHT/PPM))
    i+=3
if callback.fixture.userData != 'outer':
    print('clockwise track detected. Initiating corrections')
    temp = outer_track
    outer_track = inner_track
    inner_track = temp
    
tracks.append([outer_track,'white'])
tracks.append([inner_track,'lightblue'])

#make a box for the mouse and move it around
car = world.CreateDynamicBody(position=(200/PPM,200/PPM), angle= 0, linearDamping=.3, angularDamping = 6)
car_color = 'blue'
box = car.CreatePolygonFixture(box=(1, .5), density=1, friction=0.002)



pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Drifter Evolver')
clock = pygame.time.Clock()

def step():
        
        world.Step(1.0/60.0, 10, 10)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                quit()
    
        #change car color
        car_color = 'blue'
        for contact in car.contacts:
            if car.contacts[0].contact.touching:
                car_color = 'red' 
                
            
    
        # draw background, walls, car
        screen.fill(THECOLORS['gray'])
        for track in tracks:  
            for fixture in track[0].fixtures:
                shape = fixture.shape
                pygame.draw.polygon(screen, THECOLORS[track[1]], tfm(shape.vertices))
                
        car.position = (pygame.mouse.get_pos()[0]/PPM, pygame.mouse.get_pos()[1]/PPM)
        shape = car.fixtures[0].shape
        vertices = [(car.transform * v)*PPM for v in shape.vertices]
        pygame.draw.polygon(screen, THECOLORS[car_color], vertices)
        
        pygame.display.flip()
        clock.tick(60.0)


while 1:
    step()

