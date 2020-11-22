# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 15:26:44 2020

@author: Nick Brusco
"""
import Box2D  # The main library
# Box2D.b2 maps Box2D.b2Vec2 to vec2 (and so on)
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, vec2, chainShape, rayCastCallback)
import pygame
from pygame.locals import *
from pygame.color import THECOLORS
import pymunk.pygame_util
import numpy as np
import random
from Box2D.examples.raycast import *
import sys

class Drifter:
    name = "Drifter"
    description = "Trains a neural net to race a car around a track"
    
    def __init__(self):
        # --- constants ---
        self.PPM = 1.0 #20.0  # pixels per meter
        self.TARGET_FPS = 60
        self.TIME_STEP = 1.0 / self.TARGET_FPS
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1500, 900
        
        # --- pygame setup ---
        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption('Drifter Evolver')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.graphics = True
        
        #game variables
        self.command_mode = False
        self.command = 0
        self.playback_speed = 1
        self.frame_counter = 0 #for manipulating playback speed. only render one in every playback_speed frames
        self.max_steps_per_episode = 250
        self.stats = { 'pop': 200}
        self.pressed_keys = []
        
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
                [[-np.pi/2, 500,     100],
                [-np.pi/4,  500,     100],
                [0,         500,     100],
                [np.pi/4,   500,     100],
                [np.pi/2,   500,     100]])
        
        #checkpoints, overwritten when using trackgen
        self.cp = 0
        self.cpts = [[(0,0),(1,1)]]

        # Create world, car, track. This gets overwritten when not in manual mode so make sure you carry over any changes here to init_track
        self.world = world(gravity=(0, 0), doSleep=True)
        #self.world.setVelocityThreshold(1000000.0);
        self.car = self.world.CreateDynamicBody(position=(200,200), angle= np.pi)#, linearDamping=.1, angularDamping = 6)
        self.car_color = 'blue'
        self.box = self.car.CreatePolygonFixture(box=(4, 2), density=.4, friction=0.002)
        #self.box.massData.center = vec2(0,-10) #set center of 
        
        self.tracks = []
                
    def step(self, action = [False, False, False, False]):
        
        #reward is .05 if nothing happens, 1 if it hits a gate, 10 if it completes a lap, 0 if it hits a wall and ends simulation
        reward = .05
        flags = []
        
        #key press handler
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                quit()
                
            if event.type == KEYDOWN:
                if self.command_mode == False:
                    #if event.key == K_b:
                    #    best_mode = True
                    if event.key == K_c and self.graphics == True:
                        self.command_mode = True
                        self.command = ''
                    if (event.key == K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                        quit()
                    if (event.key == K_p):
                        for i in range(50000000): pass
                    if  event.key == K_g:
                       if self.graphics:
                           self.screen.blit(self.font.render("GRAPHICS OFF", 1, THECOLORS["red"]), (self.SCREEN_WIDTH/2-75,self.SCREEN_HEIGHT/2 + 20))
                           pygame.display.flip()
                       self.graphics = not self.graphics
                    if (event.key == K_s):
                        if self.playback_speed <16:
                            self.playback_speed *= 2
                        else:
                            self.playback_speed = 1
                
                #commands
                else:
                    if event.key == K_RETURN:
                        parsed = self.command.split(" ")
                        self.command_mode = False
                        if parsed[0] == "runtime":
                            self.max_steps_per_episode = int(parsed[1])
                            print("runtime changed to ", self.max_steps_per_episode)
                        elif parsed[0] == "generation" or parsed[0] == "population":
                            change_generation = int(parsed[1])
                            print("generation size changed to ",change_generation)
                        else:
                            print("command not recognized")
                                  
                    if event.key == K_BACKSPACE:
                        self.command = self.command[:-1]
                    else:
                        self.command += chr(event.key)
               
                       
        
        #Action: 0 = w, 1 = a, 2 = s, 3 = d
        if action[0] and 'w' not in self.pressed_keys:
            self.pressed_keys.append('w')
        if action[1] and 'a' not in self.pressed_keys:
            self.pressed_keys.append('a')
        if action[2] and 's' not in self.pressed_keys:
            self.pressed_keys.append('s')
        if action[3] and 'd' not in self.pressed_keys:
            self.pressed_keys.append('d')
                
            
        if 'w' in self.pressed_keys and not action[0]:
            self.pressed_keys.remove('w')
        if 'a' in self.pressed_keys and not action[1]:
            self.pressed_keys.remove('a')
            self.time_pressed['a'] = 0
        if 's' in self.pressed_keys and not action[2]:
            self.pressed_keys.remove('s')
        if 'd' in self.pressed_keys and not action[3]:
            self.pressed_keys.remove('d')
            self.time_pressed['d'] = 0
           
        #handle movement
        speed = self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity)
        
        for key in self.pressed_keys:
            if key == 'w':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(-2000.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 's':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(1000.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 'a':
                if self.time_pressed['a'] < 1: self.time_pressed['a'] += .013 
                self.car.ApplyTorque(-self.time_pressed['a']*speed*100, True)
            elif key == 'd':
                if self.time_pressed['d'] < 1: self.time_pressed['d'] += .013
                self.car.ApplyTorque(self.time_pressed['d']*speed*100, True)
    
        #side force when drifting
        sideforce = np.sign(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity))*min(6,abs(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity)))
        self.car.ApplyForce(-60*self.car.GetWorldVector(localVector=(0,sideforce)), self.car.GetWorldPoint(localPoint=(0.0,0.0)),True)
        
        #check checkpoint for collisions
        callback = myCallback()
        self.world.RayCast(callback, self.cpts[self.cp][0], self.cpts[self.cp][1])
        if callback.hit:
            self.cp += 1
            reward += 5
            if self.cp >= len(self.cpts): 
                self.cp=0
                self.lap += 1
                reward += 10
                if self.lap > 3:
                    flags.append('done')
        
        # check whiskers
        point1 = self.car.position
        for ray in self.rays:  
            angle = self.car.angle + np.pi + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
            
            if callback.hit:
                ray[2] = np.linalg.norm(point1 - callback.point)
            else:
                ray[2] = np.linalg.norm(point1 - point2)
                
        #change car color to red if it crashed
        if self.car.contacts == []: self.car_color = 'blue' 
        else: 
            self.car_color = 'red'
            #reward = 0
            flags.append('crashed')
                
        if self.graphics:
            self.render()
    
        self.world.Step(self.TIME_STEP, 10, 10)
        return self.get_state(), reward, flags
        
        
    def render(self):
        
        # draw background, walls, car
        self.screen.fill(THECOLORS['gray'])
        for track in self.tracks:  
            for fixture in track[0].fixtures:
                shape = fixture.shape
                #vertices = [(track[0].transform * v) for v in shape.vertices]
                #vertices = [(v[0], self.SCREEN_HEIGHT - v[1]) for v in vertices]
                pygame.draw.polygon(self.screen, THECOLORS[track[1]], shape.vertices)
                
        shape = self.car.fixtures[0].shape
        vertices = [(self.car.transform * v) for v in shape.vertices]
        pygame.draw.polygon(self.screen, THECOLORS[self.car_color], vertices)
            
        #draw checkpoint
        pygame.draw.line(self.screen, THECOLORS['green'],self.cpts[self.cp][0], self.cpts[self.cp][1], 1)
        
        
        point1 = self.car.position
        
        #draw whiskers
        for ray in self.rays:  
            angle = self.car.angle + np.pi + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
        
            if callback.hit:
                pygame.draw.circle(self.screen, THECOLORS['red'], (int(callback.point[0]),int(callback.point[1])),3)
                pygame.draw.line(self.screen, THECOLORS['red'],(point1), (callback.point), 1)
            else:
                pygame.draw.line(self.screen, THECOLORS['orange'],(point1), (point2), 1)
                
        '''
        #draw text info
        self.screen.blit(self.font.render("Generation: " + str(self.stats['pop']), 1, THECOLORS["black"]), (0,36))
        self.screen.blit(self.font.render("Individual: " + str() + " / " + str(self.stats['pop']), 1, THECOLORS["black"]), (0,54))
        
        self.screen.blit(self.font.render("Time: " + str(int((ticks%RUNTIME/30))) + " / "+ str(round(RUNTIME/30)), 1, THECOLORS["black"]), (0,72))
        self.screen.blit(self.font.render("Playback: " + str(self.playback_speed) + "x", 1, THECOLORS["black"]), (10,10))
        '''
        if self.command_mode:
            self.screen.blit(self.font.render("Cmd: " + self.command, 1, THECOLORS["green"]), (10,30))
    
        
        self.frame_counter += 1
        if self.frame_counter >= self.playback_speed:
            pygame.display.flip()
            self.frame_counter = 0
            self.clock.tick(self.TARGET_FPS)
        
    
    def reset(self):
        self.car.position= self.spawn
        self.car.angle= self.direction
        self.car.angularVelocity = 0.0
        self.car.linearVelocity = (0,0)
        
        self.frame_counter = 0
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
    
    def init_track(self, left, right, centerline, checkpoints):
        
        # --- pybox2d world setup ---
        self.world = world(gravity=(0, 0), doSleep=True)
        self.bodies = []
        self.tracks = []
        
        #track setup
        self.outer_track = self.world.CreateBody(shapes=chainShape(vertices=left))
        self.tracks.append([self.outer_track,'white'])
        self.inner_track = self.world.CreateBody(shapes=chainShape(vertices=right))
        self.tracks.append([self.inner_track,'lightblue'])
        self.centerline = centerline
        self.spawn = (int(centerline[0][0]/self.PPM), int(centerline[0][1]/self.PPM))
        self.cpts = checkpoints
        
        hyp = np.linalg.norm(np.array(self.centerline[1]) - np.array(self.centerline[0]))
        adj = (self.centerline[1][1] - self.centerline[0][1])
        
        self.direction = -(np.arccos(adj/hyp)) - np.pi/2
        
        # Create car
        self.car = self.world.CreateDynamicBody(position=self.spawn, angle= self.direction)#, linearDamping=.2, angularDamping = 6)
        self.car_color = 'blue'
        self.box = self.car.CreatePolygonFixture(box=(10, 5), density=.04)#, friction=0.2)
        self.box.massData.center = vec2(0,-10) #set center of mass
        
    
    def mstep(self, action = [False, False, False, False]):
        '''manual step for controling the car manually. basically copy/pasted self.step then deleted half of it'''
        
        flags = []
        
        #key press handler
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                quit()
                
            if event.type == KEYDOWN:
                if self.command_mode == False:
                    if event.key == K_c and self.graphics == True:
                        self.command_mode = True
                        self.command = ''
                    if (event.key == K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                        quit()
                    if (event.key == K_p):
                        for i in range(50000000): pass
                    if  event.key == K_g:
                       if self.graphics:
                           self.screen.blit(self.font.render("GRAPHICS OFF", 1, THECOLORS["red"]), (self.SCREEN_WIDTH/2-75,self.SCREEN_HEIGHT/2 + 20))
                           pygame.display.flip()
                       self.graphics = not self.graphics

                            
                    if event.key == K_w and 'w' not in self.pressed_keys:
                        self.pressed_keys.append('w')
                    if event.key == K_s and 's' not in self.pressed_keys:
                        self.pressed_keys.append('s')
                    if event.key == K_a and 'a' not in self.pressed_keys:
                        self.pressed_keys.append('a')
                    if event.key == K_d and 'd' not in self.pressed_keys:
                        self.pressed_keys.append('d')        
                    
                
                #commands
                else:
                    if event.key == K_RETURN:
                        parsed = self.command.split(" ")
                        self.command_mode = False
                        if parsed[0] == "runtime":
                            self.max_steps_per_episode = int(parsed[1])
                            print("runtime changed to ", self.max_steps_per_episode)
                        elif parsed[0] == "generation" or parsed[0] == "population":
                            change_generation = int(parsed[1])
                            print("generation size changed to ",change_generation)
                        else:
                            print("command not recognized")
                                  
                    if event.key == K_BACKSPACE:
                        self.command = self.command[:-1]
                    else:
                        self.command += chr(event.key)
               
                    
            if event.type == KEYUP:
                if event.key == K_w and 'w' in self.pressed_keys:
                    self.pressed_keys.remove('w')
                if event.key == K_s and 's' in self.pressed_keys:
                    self.pressed_keys.remove('s')
                if event.key == K_a and 'a' in self.pressed_keys:
                    self.pressed_keys.remove('a')
                    self.time_pressed['a'] = 0
                if event.key == K_d and 'd' in self.pressed_keys:
                    self.pressed_keys.remove('d')
                    self.time_pressed['d'] = 0
                       
                    
        #handle movement
        speed = self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity)
        
        for key in self.pressed_keys:
            if key == 'w':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(-1000.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 's':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(500.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 'a':
                if self.time_pressed['a'] < 1: self.time_pressed['a'] += .013 
                self.car.ApplyTorque(self.time_pressed['a']*speed*30, True)
            elif key == 'd':
                if self.time_pressed['d'] < 1: self.time_pressed['d'] += .013
                self.car.ApplyTorque(-self.time_pressed['d']*speed*30, True)
    
        #side force when drifting
        
        '''
        sideforce = np.sign(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity))*min(6,abs(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity)))
        self.car.ApplyForce(-60*self.car.GetWorldVector(localVector=(0,sideforce)), self.car.GetWorldPoint(localPoint=(0.0,0.0)),True)
        '''
        
        #check checkpoint for collisions
        callback = myCallback()
        self.world.RayCast(callback, self.cpts[self.cp][0], self.cpts[self.cp][1])
        if callback.hit:
            self.cp += 1
            if self.cp >= len(self.cpts): 
                self.cp=0
                
        #change car color to red if it crashed
        if self.car.contacts == []: self.car_color = 'blue' 
        else: 
            self.car_color = 'red'
            #reward = 0
            flags.append('crashed')
                
        if self.graphics:
            self.render()
    
        self.world.Step(self.TIME_STEP, 10, 10)
        
        
        
class myCallback(rayCastCallback):
    """This raycast collects multiple hits on car only (fixture type 2)."""

    def __repr__(self):
        return 'Multiple hits'

    def __init__(self, **kwargs):
        b2RayCastCallback.__init__(self, **kwargs)
        self.fixtures = []
        self.hit = False
        self.points = []
        self.normals = []

    def ReportFixture(self, fixture, point, normal, fraction):
        if fixture.type !=2:
            return 1.0
        self.hit = True
        self.fixtures.append(fixture)
        self.points.append(b2Vec2(point))
        self.normals.append(b2Vec2(normal))
        return 1.0
        
        
        
        