# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 17:31:47 2020

@author: Nick Brusco
"""

import Box2D  # The main library
# Box2D.b2 maps Box2D.b2Vec2 to vec2 (and so on)
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, vec2, chainShape)
import pygame
from pygame.locals import *
from pygame.color import THECOLORS
import pymunk.pygame_util
import numpy as np
import random
from Box2D.examples.raycast import *

class Drifter:
    name = "Drifter"
    description = "Trains a neural net to race a car around a track"
    
    def __init__(self):
        # --- constants ---
        self.PPM = 20.0  # pixels per meter
        self.TARGET_FPS = 60
        self.TIME_STEP = 1.0 / self.TARGET_FPS
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1500, 900
        
        # --- pygame setup ---
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption('Simple pygame example')
        self.clock = pygame.time.Clock()
        self.graphics = False
        
        # --- pybox2d world setup ---
        self.world = world(gravity=(0, 0), doSleep=True)
        self.bodies = []
        
        #track setup
        self.outer_track = self.world.CreateBody(shapes=chainShape(vertices=[(3,3), (int(self.SCREEN_WIDTH/self.PPM)-3, 3),(int(self.SCREEN_WIDTH/self.PPM)-3,int(self.SCREEN_HEIGHT/self.PPM)-3),(3,int(self.SCREEN_HEIGHT/self.PPM)-3)]))
        self.bodies.append([self.outer_track,'white'])
        self.inner_track = self.world.CreateBody(shapes=chainShape(vertices=[(17,int(self.SCREEN_HEIGHT/self.PPM)-17),(int(self.SCREEN_WIDTH/self.PPM)-17,int(self.SCREEN_HEIGHT/self.PPM)-17),(int(self.SCREEN_WIDTH/self.PPM)-17, 17),(17,17)]))
        self.bodies.append([self.inner_track,'gray'])
        
        # Create car
        self.car = self.world.CreateDynamicBody(position=(10, 15), angle= -np.pi/2, linearDamping=.4, angularDamping = 6)
        self.bodies.append([self.car,'blue'])
        self.box = self.car.CreatePolygonFixture(box=(1, .5), density=4, friction=0.2)
        self.box.massData.center = vec2(0,-10) #set center of mass
        
        self.pressed_keys = []
        self.time_pressed = {
            'w' : 0.0,
            'a' : 0.0,
            's' : 0.0,
            'd' : 0.0
            }
        
        #for whiskers
        #         angles, lengths, intercept
        self.rays = np.array( 
                [[-np.pi/2, 10,     10],
                [-np.pi/4,  15,     10],
                [0,         20,     10],
                [np.pi/4,   15,     10],
                [np.pi/2,   10,     10]])
        
        #checkpoints
        self.lap = 1
        self.cp = 0
        self.cpts = [[(3,20),(17,20)],
                [(3,25),(17,25)],  
                [(12,int(self.SCREEN_HEIGHT/self.PPM)-3),(18,int(self.SCREEN_HEIGHT/self.PPM)-17)],
                [(20,int(self.SCREEN_HEIGHT/self.PPM)-17),(20,int(self.SCREEN_HEIGHT/self.PPM)-3)],
                [(35,int(self.SCREEN_HEIGHT/self.PPM)-17),(35,int(self.SCREEN_HEIGHT/self.PPM)-3)],
                [(50,int(self.SCREEN_HEIGHT/self.PPM)-17),(50,int(self.SCREEN_HEIGHT/self.PPM)-3)],
                [(int(self.SCREEN_WIDTH/self.PPM)-17,25),(int(self.SCREEN_WIDTH/self.PPM)-3,25)],        
                [(int(self.SCREEN_WIDTH/self.PPM)-17,20),(int(self.SCREEN_WIDTH/self.PPM)-3,20)],
                [(50,17),(50,3)],
                [(35,17),(35,3)],
                [(20,17),(20,3)],
                ]
                
    def step(self, action = 0):
        
        #reward is .01 if nothing happens, 1 if it hits a gate, 10 if it completes a lap, 0 if it hits a wall and ends simulation
        reward = .002
        done = False
        flags = []
        
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                flags.append('quit')
            if event.type == KEYDOWN:
               if  event.key == K_g:
                   self.graphics = not self.graphics
                       
        
        #Action: 0 = w, 1 = a, 2 = s, 3 = d
        if action == 0 and 'w' not in self.pressed_keys:
            self.pressed_keys.append('w')
        elif action == 1 and 'a' not in self.pressed_keys:
            self.pressed_keys.append('a')
        elif action == 2 and 's' not in self.pressed_keys:
            self.pressed_keys.append('s')
        elif action == 3 and 'd' not in self.pressed_keys:
            self.pressed_keys.append('d')
                
            
        if 'w' in self.pressed_keys and action != 0:
            self.pressed_keys.remove('w')
        if 'a' in self.pressed_keys and action != 1:
            self.pressed_keys.remove('a')
            self.time_pressed['a'] = 0
        if 's' in self.pressed_keys and action != 2:
            self.pressed_keys.remove('s')
        if 'd' in self.pressed_keys and action != 3:
            self.pressed_keys.remove('d')
            self.time_pressed['d'] = 0
           
        #handle movement
        speed = self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity)
        
        for key in self.pressed_keys:
            if key == 'w':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(-200.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 's':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(100.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 'a':
                if self.time_pressed['a'] < 1: self.time_pressed['a'] += .013 
                self.car.ApplyTorque(-self.time_pressed['a']*speed*10, True)
            elif key == 'd':
                if self.time_pressed['d'] < 1: self.time_pressed['d'] += .013
                self.car.ApplyTorque(self.time_pressed['d']*speed*10, True)
    
        #side force when drifting
        sideforce = np.sign(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity))*min(6,abs(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity)))
        self.car.ApplyForce(-60*self.car.GetWorldVector(localVector=(0,sideforce)), self.car.GetWorldPoint(localPoint=(0.0,0.0)),True)
        
        #draw next checkpoint
        callback = RayCastMultipleCallback()
        self.world.RayCast(callback, self.cpts[self.cp][0], self.cpts[self.cp][1])
        if len(callback.points)>2:
            self.cp += 1
            reward = 50
            if self.cp >= len(self.cpts): 
                self.cp=0
                self.lap += 1
                reward = 100
                if self.lap > 3:
                    done = True
        
        # check whiskers
        point1 = self.bodies[2][0].position
        for ray in self.rays:  
            angle = self.bodies[2][0].angle + np.pi + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
            
            if callback.hit:
                ray[2] = np.linalg.norm(point1 - callback.point)
            else:
                ray[2] = np.linalg.norm(point1 - point2)
                
        #change car color to red if it crashed
        if self.bodies[2][0].contacts == []: self.bodies[2][1] = 'blue' 
        else: 
            self.bodies[2][1] = 'red'
            #reward = 0
            flags.append('crashed')
                
        if self.graphics:
            self.render()
    
        self.world.Step(self.TIME_STEP, 10, 10)
        return self.get_state(), reward, done, flags
        
        
    def render(self):
        
        # draw background, walls, car
        self.screen.fill(THECOLORS['gray'])
        for body in self.bodies:  # or: world.bodies
            for fixture in body[0].fixtures:
                shape = fixture.shape
                vertices = [(body[0].transform * v) * self.PPM for v in shape.vertices]
                vertices = [(v[0], self.SCREEN_HEIGHT - v[1]) for v in vertices]
                pygame.draw.polygon(self.screen, THECOLORS[body[1]], vertices)
            
        #draw checkpoint
        pygame.draw.line(self.screen, THECOLORS['green'],self.tfrm(self.cpts[self.cp][0]), self.tfrm(self.cpts[self.cp][1]), 1)
        
        #green dot on car
        point1 = self.bodies[2][0].position
        pygame.draw.circle(self.screen, THECOLORS['green'], self.tfrm(point1),3)
        
        #draw whiskers
        for ray in self.rays:  
            angle = self.bodies[2][0].angle + np.pi + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
        
            pygame.draw.circle(self.screen, THECOLORS['green'], self.tfrm(point2), 3)
        
            if callback.hit:
                pygame.draw.circle(self.screen, THECOLORS['red'], self.tfrm(callback.point),3)
                pygame.draw.line(self.screen, THECOLORS['red'],self.tfrm(point1), self.tfrm(callback.point), 1)
            else:
                pygame.draw.line(self.screen, THECOLORS['orange'],self.tfrm(point1), self.tfrm(point2), 1)
                
        pygame.display.flip()
        self.clock.tick(self.TARGET_FPS)
        
    
    def reset(self):
        self.car.position=(10, 15)
        self.car.angle= -np.pi/2
        self.car.angularVelocity = 0.0
        self.car.linearVelocity = (0,0)
        
        self.cp = 0
        self.lap = 1
        
        self.step() #to reset whisker distances, speed, etc
        
        return self.get_state()
    
    def get_state(self):
        state = [self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity),   #cars speed
                 self.car.angle % (np.pi*2),                                    #cars heading
                 self.rays[0,-1],                                               #whisker distances
                 self.rays[1,-1],
                 self.rays[2,-1],
                 self.rays[3,-1],
                 self.rays[4,-1],
                 ]
        return state
        
        
    def tfrm(self, point):
        '''transforms points from meters to pixels. also flips y axis for pygame reasons.'''
        return ( int(point[0]*self.PPM), int(self.SCREEN_HEIGHT - point[1]*self.PPM))