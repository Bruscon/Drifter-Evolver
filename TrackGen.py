# -*- coding: utf-8 -*-
"""
Track and checkpoint generator 

Created on Wed Nov 11 18:39:06 2020

@author: Nick Brusco
"""

import pygame
import pygame
from pygame.locals import *
from pygame.color import THECOLORS
import pymunk.pygame_util

import numpy as np
import sys
import math



class TrackGen:
    
    def __init__(self, dft):
        #importing a drifter object is kind of a hacky way to get all the objects defined
        #in drifter here, such as the pygame screen, resolution, etc. idk a better way to do this.
        self.dft = dft
        
        self.mode = 'intro'
        self.MAXANGLE = .3 #in radians
        self.MAXDISTANCE = 30
        self.WIDTH = 75
        self.points = []
        self.lbound = []
        self.rbound = []
        self.direction = 0
        self.angle_limit_h = (0,0)
        self.angle_limit_l = (0,0)
        
        self.intro_message = "Welcome to the track generator!\n" \
                            "Keep all parts of your track on-screen.\n"\
                            "Do not let your centerline or walls cross eachother.\n" \
                            "The track must form a complete loop.\n" \
                            "Press 'd' or backspace to remove points.\n" \
                            "Click anywhere to begin..."
        
    def step(self):
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                quit()
                
            if event.type == pygame.MOUSEBUTTONUP:
                pclicked = np.array(pygame.mouse.get_pos())
                if self.mode == 'intro':
                    self.mode = 'building'
                if self.mode == 'building':
                    self.new_point(pclicked)
                
            if event.type == KEYDOWN:   
                if event.key in [K_BACKSPACE, K_d, K_DELETE]:
                    if len(self.points) > 2:
                        self.points.pop(-1) 
                        self.lbound.pop(-1)
                        self.rbound.pop(-1)
                        self.direction = self.angle_between(self.points[-2], self.points[-1])
                        self.get_angle_limits()
                        self.mode = 'building'
                    else:
                        self.points = []
                        self.lbound = []
                        self.rbound = []
                        self.mode = 'intro'
                
                if event.key == K_RETURN and self.mode == 'done':
                    #good luck unravelling what this does, just be glad it works.
                    self.points = [list(round(b) for b in i) for i in self.points]
                    self.lbound = [list(round(b) for b in i) for i in self.lbound]
                    self.rbound = [list(round(b) for b in i) for i in self.rbound]
                    
                    cpts = []
                    for pair in self.checkpoints:
                        cpts.append(list(((round(pair[0][0]), round(pair[0][1])), (round(pair[1][0]), round(pair[1][1])))))                    
                    
                    return (self.points, self.lbound, self.rbound, cpts)
                    
                
        self.render()
        
        
    def render(self):
        
        # draw background
        self.dft.screen.fill(THECOLORS['gray'])
        
        if self.points != []:
            last_point = self.points[0]
        
        #draw angle limits
        if len(self.points) >= 2 and self.mode == 'building':
            pygame.draw.circle(self.dft.screen, THECOLORS['orange'], self.angle_limit_h,3)
            pygame.draw.circle(self.dft.screen, THECOLORS['orange'], self.angle_limit_l,3)
            pygame.draw.line(self.dft.screen, THECOLORS['orange'], self.points[-1], self.angle_limit_h,2)
            pygame.draw.line(self.dft.screen, THECOLORS['orange'], self.points[-1], self.angle_limit_l,2)
            
        #draw centerline
        for point in self.points:
            pygame.draw.circle(self.dft.screen,THECOLORS['yellow'], point,3)
            pygame.draw.line(self.dft.screen, THECOLORS['yellow'], last_point, point,2)
            last_point = point
            
        #draw walls
        if self.rbound != []:
            last_point = self.rbound[0]    
        
        for point in self.rbound:
            pygame.draw.circle(self.dft.screen, THECOLORS['white'], point,3)
            pygame.draw.line(self.dft.screen, THECOLORS['white'], last_point, point,2)
            last_point = point
            
        if self.lbound != []:
            last_point = self.lbound[0]     
        
        for point in self.lbound:
            pygame.draw.circle(self.dft.screen, THECOLORS['white'], point,3)
            pygame.draw.line(self.dft.screen, THECOLORS['white'], last_point, point,2)
            last_point = point
            
        #finish the loop if it is complete
        if self.mode == 'done':
            pygame.draw.line(self.dft.screen, THECOLORS['white'], self.rbound[0], self.rbound[-1],2)
            pygame.draw.line(self.dft.screen, THECOLORS['white'], self.lbound[0], self.lbound[-1],2)
            pygame.draw.line(self.dft.screen, THECOLORS['yellow'], self.points[0], self.points[-1],2)
            
        #draw valid mousepoint
        if self.mode == 'building':
            pygame.draw.circle(self.dft.screen,THECOLORS['blue'],self.get_vp(),3)
        
        if self.mode == 'intro':
            self.blit_text(self.dft.screen, self.intro_message, (300,200), self.dft.font)
            
        if self.mode == 'done':
            for pair in self.checkpoints:
                pygame.draw.line(self.dft.screen, THECOLORS['green'], pair[0], pair[1], 2)
            self.dft.screen.blit(self.dft.font.render("If you're happy with your track, press enter. Otherwise press delete", 1, THECOLORS["black"]), (100,400))
            
        
        pygame.display.flip()
        self.dft.clock.tick(self.dft.TARGET_FPS)
        
        
        
    def tfrm(self, point):
        '''transforms points from meters to pixels. also flips y axis for pygame reasons.'''
        return ( round(point[0]*PPM), round(SCREEN_HEIGHT - point[1]*PPM))
        
        
    def new_point(self, click):
        '''Takes a click point and places a valid next track point from it'''
        
        if len(self.points) == 0:
            self.points.append(click)
            
        elif len(self.points) == 1:
            self.points.append(self.get_vp())
            self.direction = self.angle_between(self.points[-1], click)
            #"initial unit direction" is a unit vector pointing in direction of first piece of track
            self.iud = (click - self.points[-1]) / (np.linalg.norm(click - self.points[-1]))
            self.get_angle_limits()
            
            #make right and left boundaries
            self.ud = (self.points[-1]-self.points[-2])/(np.linalg.norm(self.points[-1]-self.points[-2]))
            self.lbound.append([round(i*self.WIDTH) for i in self.rotate(self.ud,np.pi/2)] + self.points[-2])
            self.rbound.append([round(i*self.WIDTH) for i in self.rotate(self.ud,-np.pi/2)] + self.points[-2])
        
        else:
            self.points.append(self.get_vp())
            self.direction = self.angle_between(self.points[-2], self.points[-1])
            self.ud = (self.points[-1]-self.points[-2])/(np.linalg.norm(self.points[-1]-self.points[-2]))
            self.get_angle_limits()
            
            #make right and left boundaries
            self.lbound.append([round(i*self.WIDTH) for i in self.rotate(self.ud,np.pi/2)] + self.points[-2])
            self.rbound.append([round(i*self.WIDTH) for i in self.rotate(self.ud,-np.pi/2)] + self.points[-2])
            
            
            #check if this last point can complete the track:
            if np.linalg.norm(self.points[0] - self.points[-1]) < self.MAXDISTANCE*1.3:

                #Get angle between two unit vectors. Dont ask how it works.
                turn = math.atan2(self.ud[0]*self.iud[1] - self.ud[1]*self.iud[0], self.ud[0]*self.iud[0] + self.ud[1]*self.iud[1])
                
                if turn > self.MAXANGLE:
                    print('ERROR: track cannot loop here, angle too sharp. Delete a few points and try again.')
                elif turn < -self.MAXANGLE:
                    print('ERROR: track cannot loop here, angle too sharp. Delete a few points and try again.')
                elif len(self.points) >=4:
                    print('Track complete!')
                    self.generate_checkpoints()
                    self.mode = 'done'
        
    def get_vp(self):
        '''takes mouse location and outputs a valid next point to render'''
        
        if self.points == []: #just return the mouse position if its the first point
            return pygame.mouse.get_pos()
        
        distance = max(np.linalg.norm(pygame.mouse.get_pos()-self.points[-1]),.01) #max to avoid div by 0 error
        uv = (pygame.mouse.get_pos()-self.points[-1])/distance #unit vector from last point to mouse
        
        if len(self.points)== 1: #if its the second point, there is no angle restriction
            vp = (uv*self.MAXDISTANCE) + self.points[-1]
            return vp.astype(int)
        
        else: #all other points need angle restriction 
            vp = (uv*self.MAXDISTANCE) + self.points[-1]
            
            #'unit direction' is the unit vector between last two points
            ud = (self.points[-1]-self.points[-2])/(np.linalg.norm(self.points[-1]-self.points[-2]))
            #Get angle between two unit vectors. Dont ask how it works.
            turn = math.atan2(ud[0]*uv[1] - ud[1]*uv[0], ud[0]*uv[0] + ud[1]*uv[1])

            if turn > self.MAXANGLE:
                vp =  self.angle_limit_h
            elif turn < -self.MAXANGLE:
                vp =  self.angle_limit_l
                
            return vp.astype(int)
        
    def angle_between(self, p1, p2):
        return math.atan2((p2-p1)[1], (p2-p1)[0])
    
    def get_angle_limits(self):
        self.angle_limit_h = (round(self.MAXDISTANCE*math.cos(self.direction + self.MAXANGLE)), round(self.MAXDISTANCE*math.sin(self.direction + self.MAXANGLE))) + self.points[-1]
        self.angle_limit_l = (round(self.MAXDISTANCE*math.cos(self.direction - self.MAXANGLE)), round(self.MAXDISTANCE*math.sin(self.direction - self.MAXANGLE))) + self.points[-1]
        
    def rotate(self, vec, theta):
        '''rotates a vector vec ccw by theta radians'''
        c,s = np.cos(theta) , np.sin(theta)
        R = np.array(((c,-s),(s,c)))
        return (np.dot(R, vec))
    
    def blit_text(self, surface, text, pos, font, color=pygame.Color('black')):
        words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words.
        space = font.size(' ')[0]  # The width of a space.
        max_width, max_height = surface.get_size()
        x, y = pos
        for line in words:
            for word in line:
                word_surface = font.render(word, 0, color)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width:
                    x = pos[0]  # Reset the x.
                    y += word_height  # Start on new row.
                surface.blit(word_surface, (x, y))
                x += word_width + space
            x = pos[0]  # Reset the x.
            y += word_height  # Start on new row.
            
    def generate_checkpoints(self):
        '''takes the three lists of points (rbound, lbound, points) and generates
        all the checkpoints for the drifter in a new list called self.checkpoints'''
        
        GATESPERPOINT = 5 #number of gates drawn per point set in self.points
        self.checkpoints = []
            
        for i in range(len(self.points)-1):
            if i == 0:
                lastl = self.lbound[0]
                lastr = self.rbound[0]
                continue
            
            xleft = np.linspace(lastl[0], self.lbound[i][0], GATESPERPOINT).astype(int)
            yleft = np.linspace(lastl[1], self.lbound[i][1], GATESPERPOINT).astype(int)
            xright = np.linspace(lastr[0], self.rbound[i][0], GATESPERPOINT).astype(int)
            yright = np.linspace(lastr[1], self.rbound[i][1], GATESPERPOINT).astype(int)
            h = zip(zip(xleft,yleft), zip(xright,yright))
            
            for j in h:
                self.checkpoints.append(j)
            
            lastl = self.lbound[i]
            lastr = self.rbound[i]
            
        #now do the checkpoints between the last and first points in the lists
        FUDGEFACTOR = np.linalg.norm(self.points[0]-self.points[-2])/self.MAXDISTANCE
        #fudge factor is a measure of how much longer/shorter the final point is from the first point
        #used to make sure gates are evenly spaced even in the last segment
        xleft = np.linspace(self.lbound[-1][0], self.lbound[0][0], round(GATESPERPOINT*FUDGEFACTOR)).astype(int)
        yleft = np.linspace(self.lbound[-1][1], self.lbound[0][1], round(GATESPERPOINT*FUDGEFACTOR)).astype(int)
        xright = np.linspace(self.rbound[-1][0], self.rbound[0][0], round(GATESPERPOINT*FUDGEFACTOR)).astype(int)
        yright = np.linspace(self.rbound[-1][1], self.rbound[0][1], round(GATESPERPOINT*FUDGEFACTOR)).astype(int)
        h = zip(zip(xleft,yleft), zip(xright,yright))
        
        for j in h:
                self.checkpoints.append(j)

        
        
if __name__ == "__main__": 
    
    tg = TrackGen()
    
    PPM = 20.0  # pixels per meter
    TARGET_FPS = 60
    TIME_STEP = 1.0 / TARGET_FPS
    SCREEN_WIDTH, SCREEN_HEIGHT = 1500, 900
    
    # --- pygame setup ---
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    pygame.display.set_caption('Track Generator')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Times", 42)
    
    
    while(1):
        tg.step()