#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame

import Box2D  # The main library
# Box2D.b2 maps Box2D.b2Vec2 to vec2 (and so on)
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, vec2, chainShape)
from pygame.locals import *
from pygame.color import THECOLORS
import pymunk.pygame_util
import numpy as np
import random
from Box2D.examples.raycast import *

# --- constants ---
PPM = 20.0  # pixels per meter
TARGET_FPS = 60
TIME_STEP = 1.0 / TARGET_FPS
SCREEN_WIDTH, SCREEN_HEIGHT = 1500, 900

# --- pygame setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Simple pygame example')
clock = pygame.time.Clock()

# --- pybox2d world setup ---
world = world(gravity=(0, 0), doSleep=True)
bodies = []

#track setup
outer_track = world.CreateBody(shapes=chainShape(vertices=[(3,3), (int(SCREEN_WIDTH/PPM)-3, 3),(int(SCREEN_WIDTH/PPM)-3,int(SCREEN_HEIGHT/PPM)-3),(3,int(SCREEN_HEIGHT/PPM)-3)]))
bodies.append([outer_track,'white'])
inner_track = world.CreateBody(shapes=chainShape(vertices=[(17,int(SCREEN_HEIGHT/PPM)-17),(int(SCREEN_WIDTH/PPM)-17,int(SCREEN_HEIGHT/PPM)-17),(int(SCREEN_WIDTH/PPM)-17, 17),(17,17)]))
bodies.append([inner_track,'gray'])

# Create car
car = world.CreateDynamicBody(position=(10, 15), angle= -np.pi/2, linearDamping=.4, angularDamping = 6)
bodies.append([car,'blue'])
box = car.CreatePolygonFixture(box=(1, .5), density=4, friction=0.2)
box.massData.center = vec2(0,-10) #set center of mass

pressed_keys = []
time_pressed = {
    'w' : 0.0,
    'a' : 0.0,
    's' : 0.0,
    'd' : 0.0
    }

#for whiskers
#         angles, lengths, intercept
rays = [[-np.pi/2,  10,     0],
        [-np.pi/4,  15,     0],
        [0,         20,     0],
        [np.pi/4,   15,     0],
        [np.pi/2,   10,     0]]

#checkpoints
cp =15
cpts = []
NUM_CHECKPOINTS = 50
center = (int(SCREEN_WIDTH/PPM/2),int(SCREEN_HEIGHT/PPM/2))
for i in range(NUM_CHECKPOINTS):
    cpts.append([center, (0, int(SCREEN_HEIGHT*i/NUM_CHECKPOINTS/PPM))])
for i in range(NUM_CHECKPOINTS):
    cpts.append([center, ( int(SCREEN_WIDTH*i/NUM_CHECKPOINTS/PPM), SCREEN_HEIGHT/PPM)])
for i in range(NUM_CHECKPOINTS):
    cpts.append([center, (SCREEN_WIDTH/PPM, int(SCREEN_HEIGHT/PPM - (SCREEN_HEIGHT*i/NUM_CHECKPOINTS/PPM)))])
for i in range(NUM_CHECKPOINTS):
    cpts.append([center, ( int(SCREEN_WIDTH/PPM - (SCREEN_WIDTH*i/NUM_CHECKPOINTS/PPM)), 0)])


def tfrm(point):
    '''transforms points from meters to pixels. also flips y axis for pygame reasons.'''
    return ( int(point[0]*PPM), int(SCREEN_HEIGHT - point[1]*PPM))

# --- main game loop ---
running = True
while running:
    # Check the event queue
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            # The user closed the window or pressed escape
            running = False
            
        if event.type == KEYDOWN:   
            if event.key == K_w and 'w' not in pressed_keys:
                pressed_keys.append('w')
            if event.key == K_s and 's' not in pressed_keys:
                pressed_keys.append('s')
            if event.key == K_a and 'a' not in pressed_keys:
                pressed_keys.append('a')
            if event.key == K_d and 'd' not in pressed_keys:
                pressed_keys.append('d')
                
            
        if event.type == KEYUP:
            if event.key == K_w and 'w' in pressed_keys:
                pressed_keys.remove('w')
            if event.key == K_s and 's' in pressed_keys:
                pressed_keys.remove('s')
            if event.key == K_a and 'a' in pressed_keys:
                pressed_keys.remove('a')
                time_pressed['a'] = 0
            if event.key == K_d and 'd' in pressed_keys:
                pressed_keys.remove('d')
                time_pressed['d'] = 0
       
    #handle movement
    speed = car.GetWorldVector((1,0)).dot(car.linearVelocity)
    
    for key in pressed_keys:
        if key == 'w':
            car.ApplyForce(car.GetWorldVector(localVector=(-200.0, 0.0)), car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
        elif key == 's':
            car.ApplyForce(car.GetWorldVector(localVector=(100.0, 0.0)), car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
        elif key == 'a':
            if time_pressed['a'] < 1: time_pressed['a'] += .013 
            car.ApplyTorque(-time_pressed['a']*speed*10, True)
        elif key == 'd':
            if time_pressed['d'] < 1: time_pressed['d'] += .013
            car.ApplyTorque(time_pressed['d']*speed*10, True)

    #side force when drifting
    sideforce = np.sign(car.GetWorldVector((1,0)).cross(car.linearVelocity))*min(6,abs(car.GetWorldVector((1,0)).cross(car.linearVelocity)))
    car.ApplyForce(-60*car.GetWorldVector(localVector=(0,sideforce)), car.GetWorldPoint(localPoint=(0.0,0.0)),True)
    
    
    screen.fill(THECOLORS['gray'])
        # Draw the world
    for body in bodies:  
        for fixture in body[0].fixtures:
            shape = fixture.shape
            vertices = [(body[0].transform * v) * PPM for v in shape.vertices]
            vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]
            pygame.draw.polygon(screen, THECOLORS[body[1]], vertices)
    
    
    #change car color to red if it crashed
    if bodies[2][0].contacts == []: bodies[2][1] = 'blue' 
    else: bodies[2][1] = 'red'            
            
    #draw next checkpoint
    callback = RayCastMultipleCallback()
    world.RayCast(callback, cpts[cp][0], cpts[cp][1])
    if len(callback.points)>2:
        print(callback.fixtures)
        cp += 1
        if cp >= len(cpts): cp=0
    pygame.draw.line(screen, THECOLORS['green'],tfrm(cpts[cp][0]), tfrm(cpts[cp][1]), 1)



    # draw what the whiskers can see
    point1 = bodies[2][0].position
    pygame.draw.circle(screen, THECOLORS['green'], tfrm(point1),3)
    for ray in rays:  
        angle = bodies[2][0].angle + np.pi + ray[0]
        d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
        point2 = point1 + d

        callback = RayCastMultipleCallback()
        world.RayCast(callback, point1, point2)
    
        pygame.draw.circle(screen, THECOLORS['green'], tfrm(point2), 3)
    
        if callback.hit:
            pygame.draw.circle(screen, THECOLORS['red'], tfrm(callback.points[0]),3)
            pygame.draw.line(screen, THECOLORS['red'],tfrm(point1), tfrm(callback.points[0]), 1)
            ray[2] = np.linalg.norm(point1 - callback.points[0])
        else:
            pygame.draw.line(screen, THECOLORS['orange'],tfrm(point1), tfrm(point2), 1)
            ray[2] = np.linalg.norm(point1 - point2)
            

    world.Step(TIME_STEP, 10, 10)
    pygame.display.flip()
    clock.tick(TARGET_FPS)

pygame.quit()
