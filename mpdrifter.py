# -*- coding: utf-8 -*-
"""
Created on Sat Dec  5 21:06:18 2020

@author: Nick Brusco
"""

import Box2D  # The main library
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, vec2, chainShape, rayCastCallback)
import numpy as np
import random
import neat

import ntools

from Box2D.examples.raycast import RayCastClosestCallback, b2RayCastCallback
import sys, os


class MPDrifter:
    name = "Multiprocessing Drifter"
    description = "The multiprocessing-compatible version of Drifter"
    
    def __init__(self, q, r, dc, track, trials, config):
        #setup MP
        self.q = q      #queue for unsolved genomes
        self.r = r      #queue for solved fitness scores
        self.dc = dc    #queue for direct comms to this subprocess
        
        
        self.track = track
        self.config = config
        self.crashbad = True #whether crashing ends the round
        self.trial = 0
        self.trials = trials
        
        self.TARGET_FPS = 60
        self.TIME_STEP = 1.0 / self.TARGET_FPS
        
        # --- constants ---
        self.PPM = 10.0  # pixels per meter
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1300, 700

        self.max_steps_per_episode = 1000
        self.stats = { 'pop': 200}
        
        self.pressed_keys = []
        self.time_pressed = {
            'w' : 0.0,
            'a' : 0.0,
            's' : 0.0,
            'd' : 0.0
            }
        
        #for whiskers
        #         angles, lengths, intercept, normal dot direction 
        angles = [0, 7*np.pi/8, -7*np.pi/8, np.pi/2, -np.pi/2, *[float(x) for x in np.split(np.linspace(-np.pi/4, np.pi/4, 6), 6)]]
        self.rays = np.array([[x, 130, 100, 0] for x in angles])
        
        #self.init_track(*self.track)
        
                
    def step(self, action = [False, False, False, False]):
        
        #reward is .05 if nothing happens, 1 if it hits a gate, 10 if it completes a lap, 0 if it hits a wall and ends simulation
        reward = .05
        flags = []
        
        
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
        #the next 30 lines took days of tuning to get right. dont fuck with it.
        fw_speed = (self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity))
        
        for key in self.pressed_keys:
            if key == 'w':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(120.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 's':
                #braking power is a function of speed, reverse is just fixed force
                if fw_speed > 0 :
                    bp = max(min(400.0,abs(fw_speed)*5.0),100.0)
                else: bp = 60.0
                
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(-bp, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 'a':
                if self.time_pressed['a'] < 1: self.time_pressed['a'] += 1 #in effect disabling "time pressed" feature 
                self.car.ApplyTorque(-min(fw_speed*self.time_pressed['a']*.7,25), True)
                #hard limit on turning force (min 20 statement) to prevent oversteer at high speed
            elif key == 'd':
                if self.time_pressed['d'] < 1: self.time_pressed['d'] += 1
                self.car.ApplyTorque(min(fw_speed*self.time_pressed['d']*.7,25), True)
    
        #side force when drifting
        MAX_SIDEFORCE = 15
        sideforce = self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity)
        if sideforce > MAX_SIDEFORCE: sideforce = MAX_SIDEFORCE
        elif sideforce < -MAX_SIDEFORCE: sideforce = -MAX_SIDEFORCE
        self.car.ApplyForce(-12*self.car.GetWorldVector(localVector=(abs(sideforce/5),sideforce)), self.car.GetWorldPoint(localPoint=(0.0,0.0)),True)
        #force in x ensures drifting doesnt penalize your speed too bad ^           ^

                    
        #check checkpoint for collisions
        was_hit = True
        while was_hit:                  #to prevent gate skipping at high speed
            callback = myCallback()
            self.world.RayCast(callback, (self.cpts[self.cp][0]), (self.cpts[self.cp][1]))
            if callback.hit:
                reward = 10
                self.cp += 1
                if self.cp >= len(self.cpts): 
                    self.cp=0
            else: was_hit = False
        
        # check whiskers
        point1 = self.car.position
        for ray in self.rays:  
            angle = self.car.angle + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
            
            if callback.hit:
                ray[2] = np.linalg.norm(point1 - callback.point)
                ray[3] = np.dot((np.cos(self.car.fixtures[0].body.angle) , np.sin(self.car.fixtures[0].body.angle)) , callback.normal)
            else:
                ray[2] = np.linalg.norm(point1 - point2)
                
                
        #change car color to red if it crashed
        if self.crashbad:       #only if crashing is bad though
            for contact in self.car.contacts:
                if self.car.contacts[0].contact.touching: #AABB collision bug fix, keep it
                    self.car_color = 'red'
                    flags.append('crashed')
    
        self.world.Step(self.TIME_STEP, 2, 2)
        return self.get_state(), reward, flags
        
    
    def reset(self):
        #spawn point index
        spi = self.trials[self.trial]
        self.car.position= self.rtfm(self.centerline[spi])
        self.car.angle = np.arctan2(self.centerline[spi+1][1] - self.centerline[spi][1], self.centerline[spi+1][0] - self.centerline[spi][0])
        self.car.angularVelocity = 0.0
        self.car.linearVelocity = (0,0)
        
        self.frame_counter = 0
        self.cp = spi*5 #5 comes from track gen checkpoints per point set
        self.lap = 1
        
        self.step() #to reset whisker distances, speed, etc
        
        return self.get_state()
    
    def get_state(self):
        state = [self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity),   #cars speed
                 *np.split(self.rays[:,2],len(self.rays[:,2])),*np.split(self.rays[:,3],len(self.rays[:,3]))
                 ] #whisker distances,                  whisker normals
        return state
    
    def init_track(self, centerline, left, right, checkpoints):
        
        # --- pybox2d world setup ---
        self.world = world(gravity=(0, 0), doSleep=True)
        self.bodies = []
        self.tracks = []
        
        #track setup
        outer_track = self.world.CreateBody(shapes=chainShape(vertices=self.rtfm(left)))
        inner_track = self.world.CreateBody(shapes=chainShape(vertices=self.rtfm(right)))
        self.centerline = centerline
        self.spawn = self.rtfm(self.centerline[random.randint(0,len(self.centerline)-2)])
        self.cpts = list(self.rtfm(x) for x in checkpoints) #unlike left and right tracks, center is stored as meters instead of pix.
        #this is because it is accessed as meters by physics engine every loop.
        
        #this next bit decides whether to flip left and right to make sure we can handle clockwise AND
        #counterclockwise tracks in the next bit. Theres probably a faster way to do it but this block
        #only runs once so who cares. The idea is to shoot a ray across the screen until it hits a track,
        #and whichever track it contacts first is the outer track (left track)
        outer_track.fixtures[0].userData = 'outer'
        callback = RayCastClosestCallback()
        i=0
        while callback.hit == False:  
            self.world.RayCast(callback, (i-10,-10), (i-10,self.SCREEN_HEIGHT/self.PPM))
            i+=3
        if callback.fixture.userData != 'outer':
            print('clockwise track detected. Initiating corrections')
            temp = outer_track
            outer_track = inner_track
            inner_track = temp
            
        self.tracks.append([outer_track,'white'])
        self.tracks.append([inner_track,'lightblue'])
        
        self.direction = np.arctan2(centerline[1][1] - centerline[0][1], centerline[1][0] - centerline[0][0])
        
        # Create car
        self.car = self.world.CreateDynamicBody(position=self.spawn, angle= self.direction, linearDamping=.3, angularDamping = 6)
        self.car_color = 'blue'
        self.box = self.car.CreatePolygonFixture(box=(1, .5), density=1, friction=0.002)
        
        self.reset() #move car to a random location
        
    def mp(self):
        '''multiprocess! this function alone runs infinitely as a separate process until terminated.'''
        
        self.init_track(*self.track)  #need to do this here and not in __init__ for some reason
        self.pid = os.getpid()
        
        while (1):
            fromq = self.q.get() #take from the queue, or wait if none are available
            #cmd = self.c.get_nowait()
            
            if fromq == None: #if the genome is None, kill yourself
                sys.exit()
                return 0
            if fromq == 'read dc': 
                self.process_command()
                continue
                
            genome_id, genome = fromq
            nn = neat.nn.RecurrentNetwork.create(genome, self.config)
            genome.fitness = 0
            fitness = 0
            
            self.trial = 0
            for trl in self.trials:
                self.reset()
                self.trial += 1
                done = False      
                flags = []
                for timestep in range(1, self.max_steps_per_episode):
                    
                    #run inputs through neural net
                    outputs = nn.activate(self.get_state())
                    
                    #convert probabilities to binary key press outputs
                    keys = []
                    for key in outputs:
                        keys.append(key > 0)
                    
                    #apply outputs to game 
                    state, reward, flags = self.step(keys)
                    #print('pid: ', os.getpid(), ', reward: ',reward)
                    
                    for flag in flags:
                        if flag == 'crashed':
                            #print('pid: ', os.getpid(), ' crashed! ')
                            done = True
                            break
                        
                    fitness += reward
                    #print('pid: ', os.getpid(), ', fitness: ',fitness)
            
                    if done:
                        break
            
            genome.fitness = fitness
            #print('pid: ', os.getpid(), ', final fitness: ',genome.fitness)
            self.r.put( (genome_id, genome) )     #put fitness in results queue to signal that we're done
            
        
    def tfm(self, meters):
        '''transforms from meters to pixels for single values and points'''
        if type(meters) == int:
            return meters*self.PPM
        elif type(meters) == list:
            rv = []
            for item in meters:
                if type(item) in [list,tuple]: #handle lists of lists of points
                    rv.append([item[0]*self.PPM,item[1]*self.PPM])
                else:
                    rv.append(item*self.PPM)
            return rv
        else:
            return None
        
    def rtfm(self, pix):
        '''reverse transforms a list of points from pixels to meters'''
        rv = []
        if type(pix[0]) in[int]:
            return [pix[0]/self.PPM, pix[1]/self.PPM]
        
        for point in pix:
            rv.append([(point[0]/self.PPM),(point[1]/self.PPM)])
        return rv
        
    def process_command(self):
        arg = self.dc.get()
        #print(f'process {os.getpid()} recieved command {arg}')
        commands = {
            'new track'     : self.new_track,
            'new config'    : self.new_config,
            'start points'  : self.start_points,
            'runtime'       : self.new_runtime,
            'crashbad'      : self.set_crashbad
        }
        func = commands.get(arg[0])
        assert func != None
        func(arg[1:])

        self.dc.task_done() #allow main process to continue
            
    def new_track(self, args):
        ''' untested'''
        self.init_track(*args)
    
    def new_runtime(self, arg):
        self.max_steps_per_episode = int(arg[0])
        
    def new_config(self,args):
        '''not implemented yet'''
        pass
    
    def set_crashbad(self, args):
        if args[0].lower() in ['1','true','t','yes']:
            self.crashbad = True
        elif args[0].lower() in ['0','false', 'f','no']:
            self.crashbad = False
        else:
            raise Exception(f'recieved a bad crashbad argument: {args[0]}')
        
    def start_points(self, arg):
        self.trials = arg[0]
    
        
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
        self.points.append(vec2(point))
        self.normals.append(vec2(normal))
        return 1.0
        
        
        
        