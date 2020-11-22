#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An attempt at some simple, self-contained pygame-based examples.

Example 01

In short:
One static body: a big polygon to represent the ground
One dynamic body: a rotated big polygon
And some drawing code to get you going.
"""
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
PPM = 1.0 #20.0  # pixels per meter
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
    
    #change car color to red if it crashed
    if bodies[2][0].contacts == []: bodies[2][1] = 'blue' 
    else: bodies[2][1] = 'red'
    

    # Draw the world
    screen.fill(THECOLORS['gray'])
    for body in bodies:  # or: world.bodies
        for fixture in body[0].fixtures:
            shape = fixture.shape
            vertices = [(body[0].transform * v) * PPM for v in shape.vertices]
            vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]
            pygame.draw.polygon(screen, THECOLORS[body[1]], vertices)
            
            

    # Make Box2D simulate the physics of our world for one step.
    # Instruct the world to perform a single step of simulation. It is
    # generally best to keep the time step and iterations fixed.
    # See the manual (Section "Simulating the World") for further discussion
    # on these parameters and their implications.
    world.Step(TIME_STEP, 10, 10)

    # Flip the screen and try to keep at the target FPS
    pygame.display.flip()
    clock.tick(TARGET_FPS)

pygame.quit()
