# -*- coding: utf-8 -*-
"""
Modified Drifter class that inherits from BaseDrifter.

@author: Nick Brusco
"""

import Box2D
from Box2D.examples.raycast import RayCastClosestCallback

import pygame
from pygame.locals import *
from pygame.color import THECOLORS
import sys
import random
import numpy as np

from BaseDrifter import BaseDrifter, myCallback

class Drifter(BaseDrifter):
    """
    Drifter class for the main application with visualization capabilities.
    Inherits shared functionality from BaseDrifter.
    """
    
    name = "Drifter"
    description = "Trains a neural net to race a car around a track"
    
    def __init__(self):
        # Initialize the base class
        super().__init__()
        
        # --- pygame setup ---
        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption('Drifter Evolver')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.graphics = True
        
        # UI state variables
        self.command_mode = False
        self.command = 0
        self.cmd = []
        self.playback_speed = 1
        self.frame_counter = 0  # For manipulating playback speed
        
        # Create world, car, track. This gets overwritten when not in manual mode
        self.init_base_environment()
                
    def init_base_environment(self):
        """Initialize a simple environment for manual mode."""
        self.world = Box2D.b2.world(gravity=(0, 0), doSleep=True)
        self.car = self.world.CreateDynamicBody(position=(200/self.PPM, 200/self.PPM), angle=0, linearDamping=.3, angularDamping=6)
        self.car_color = 'blue'
        self.box = self.car.CreatePolygonFixture(box=(1, .5), density=1, friction=0.002)
        self.tracks = []
        
    def step(self, action=[False, False, False, False]):
        """
        Override step method to handle UI events and rendering.
        """
        # Process UI events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == KEYDOWN:
                if self.command_mode == False:
                    if event.key == K_c and self.graphics == True:
                        self.command_mode = True
                        self.command = ''
                    if (event.key == K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                    if (event.key == K_p):
                        for i in range(50000000): pass
                    if event.key == K_g:
                       if self.graphics:
                           self.screen.blit(self.font.render("GRAPHICS OFF", 1, THECOLORS["red"]), 
                                          (self.SCREEN_WIDTH/2-75, self.SCREEN_HEIGHT/2 + 20))
                           pygame.display.flip()
                       self.graphics = not self.graphics
                    if (event.key == K_s):
                        if self.playback_speed < 16:
                            self.playback_speed *= 2
                        else:
                            self.playback_speed = 1
                
                # Handle command mode
                else:
                    if event.key == K_RETURN:
                        parsed = self.command.strip().split(" ")
                        self.cmd = parsed  # This is for the other processes, see get_commands()
                        self.command_mode = False
                        if parsed[0] == "runtime":
                            self.max_steps_per_episode = int(parsed[1])
                            print("runtime changed to ", self.max_steps_per_episode)
                        elif parsed[0] == "generation" or parsed[0] == "population":
                            change_generation = int(parsed[1])
                            print("generation size changed to ", change_generation)
                        elif parsed[0] == 'crashbad':
                            if parsed[1].lower() in ['1', 'true', 't', 'yes']:
                                self.crashbad = True
                            elif parsed[1].lower() in ['0', 'false', 'f', 'no']:
                                self.crashbad = False
                        else:
                            print("command not recognized")
                                  
                    if event.key == K_BACKSPACE:
                        self.command = self.command[:-1]
                    else:
                        self.command += chr(event.key)
        
        # Call the base class step function
        state, reward, flags = super().step(action)
        
        # Render if graphics are enabled
        if self.graphics:
            self.frame_counter += 1
            if self.frame_counter >= self.playback_speed:
                self.render()
                self.frame_counter = 0
                
        return state, reward, flags
        
    def render(self):
        """Render the current state to the pygame screen."""
        # Draw background, walls, car
        self.screen.fill(THECOLORS['gray'])
        for track in self.tracks:  
            for fixture in track[0].fixtures:
                shape = fixture.shape
                pygame.draw.polygon(self.screen, THECOLORS[track[1]], self.tfm(shape.vertices))
                
        shape = self.car.fixtures[0].shape
        vertices = [(self.car.transform * v)*self.PPM for v in shape.vertices]
        pygame.draw.polygon(self.screen, THECOLORS[self.car_color], vertices)
            
        # Draw checkpoint
        pygame.draw.line(self.screen, THECOLORS['green'], 
                        self.tfm(self.cpts[self.cp][0]), self.tfm(self.cpts[self.cp][1]), 1)
        
        # Draw whiskers
        point1 = self.car.position
        for ray in self.rays:  
            angle = self.car.angle + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
        
            if callback.hit:
                pygame.draw.circle(self.screen, THECOLORS['red'], 
                                  (int(callback.point[0]*self.PPM), int(callback.point[1]*self.PPM)), 3)
                pygame.draw.line(self.screen, THECOLORS['red'], 
                                (point1*self.PPM), (callback.point*self.PPM), 1)
                pygame.draw.line(self.screen, THECOLORS['black'], 
                                self.tfm(callback.point), self.tfm(callback.point + callback.normal))
            else:
                pygame.draw.line(self.screen, THECOLORS['orange'], 
                                (point1*self.PPM), (point2*self.PPM), 1)
                
        # Draw command mode text if active
        if self.command_mode:
            self.screen.blit(self.font.render("Cmd: " + self.command, 1, THECOLORS["green"]), (10, 30))
    
        pygame.display.flip()
        self.clock.tick(self.TARGET_FPS)  # Keep this change, it fixes fast playback low framerate bug
    
    def mstep(self, action=[False, False, False, False]):
        """Manual step for controlling the car manually."""
        flags = []
        
        # Process events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == KEYDOWN:
                if self.command_mode == False:
                    if event.key == K_c and self.graphics == True:
                        self.command_mode = True
                        self.command = ''
                    if (event.key == K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                    if (event.key == K_p):
                        for i in range(50000000): pass
                    if event.key == K_g:
                       if self.graphics:
                           self.screen.blit(self.font.render("GRAPHICS OFF", 1, THECOLORS["red"]), 
                                          (self.SCREEN_WIDTH/2-75, self.SCREEN_HEIGHT/2 + 20))
                           pygame.display.flip()
                       self.graphics = not self.graphics
                    if event.key == K_r:
                        self.reset()
                            
                    if event.key == K_w and 'w' not in self.pressed_keys:
                        self.pressed_keys.append('w')
                    if event.key == K_s and 's' not in self.pressed_keys:
                        self.pressed_keys.append('s')
                    if event.key == K_a and 'a' not in self.pressed_keys:
                        self.pressed_keys.append('a')
                    if event.key == K_d and 'd' not in self.pressed_keys:
                        self.pressed_keys.append('d')        
                
                # Handle command mode
                else:
                    if event.key == K_RETURN:
                        parsed = self.command.split(" ")
                        self.command_mode = False
                        if parsed[0] == "runtime":
                            self.max_steps_per_episode = int(parsed[1])
                            print("runtime changed to ", self.max_steps_per_episode)
                        elif parsed[0] == "generation" or parsed[0] == "population":
                            change_generation = int(parsed[1])
                            print("generation size changed to ", change_generation)
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
        
        # Handle movement physics
        fw_speed = (self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity))
        
        for key in self.pressed_keys:
            if key == 'w':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(120.0, 0.0)), 
                                   self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 's':
                # Braking power is a function of speed, reverse is just fixed force
                if fw_speed > 0:
                    bp = max(min(400.0, abs(fw_speed)*5.0), 100.0)
                else: 
                    bp = 60.0
                
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(-bp, 0.0)), 
                                   self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 'a':
                if self.time_pressed['a'] < 1: 
                    self.time_pressed['a'] += 1  # In effect disabling "time pressed" feature 
                self.car.ApplyTorque(-min(fw_speed*self.time_pressed['a']*.7, 25), True)
            elif key == 'd':
                if self.time_pressed['d'] < 1: 
                    self.time_pressed['d'] += 1
                self.car.ApplyTorque(min(fw_speed*self.time_pressed['d']*.7, 25), True)
    
        # Side force when drifting
        MAX_SIDEFORCE = 15
        sideforce = self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity)
        if sideforce > MAX_SIDEFORCE: 
            sideforce = MAX_SIDEFORCE
        elif sideforce < -MAX_SIDEFORCE: 
            sideforce = -MAX_SIDEFORCE
        self.car.ApplyForce(-12*self.car.GetWorldVector(localVector=(abs(sideforce/5), sideforce)), 
                           self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)

        # Check checkpoint for collisions
        was_hit = True
        while was_hit:  # To prevent gate skipping at high speed
            callback = myCallback()
            self.world.RayCast(callback, (self.cpts[self.cp][0]), (self.cpts[self.cp][1]))
            if callback.hit:
                self.cp += 1
                if self.cp >= len(self.cpts): 
                    self.cp = 0
            else: 
                was_hit = False
        
        # Change car color to red if it crashed
        self.car_color = 'blue'
        for contact in self.car.contacts:
            if self.car.contacts[0].contact.touching:  # AABB collision bug fix
                self.car_color = 'red'
                flags.append('crashed')
                
        # Render if graphics enabled
        if self.graphics:
            self.render()
    
        # Advance physics simulation
        self.world.Step(self.TIME_STEP, 2, 2)
    
    def get_commands(self):
        """
        Holds a command until the main loop reads it and sends it off to the
        subprocesses. Then reset the command.
        """
        if self.cmd == []:
            return []
        else:
            rv = self.cmd
            self.cmd = []
            return rv