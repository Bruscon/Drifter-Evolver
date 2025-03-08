# -*- coding: utf-8 -*-
"""
Base Drifter class that serves as the foundation for both Drifter and MPDrifter classes.
This contains all the shared functionality to avoid code duplication.

@author: Nick Brusco
"""

import Box2D  # The main library
# Box2D.b2 maps Box2D.b2Vec2 to vec2 (and so on)
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, vec2, chainShape, rayCastCallback)
import numpy as np
from Box2D.examples.raycast import RayCastClosestCallback, b2RayCastCallback
import sys

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
        if fixture.type != 2:
            return 1.0
        self.hit = True
        self.fixtures.append(fixture)
        self.points.append(vec2(point))
        self.normals.append(vec2(normal))
        return 1.0

class BaseDrifter:
    """
    Base class containing all shared functionality between Drifter and MPDrifter.
    """
    
    def __init__(self):
        # --- constants ---
        self.PPM = 10.0  # pixels per meter
        self.TARGET_FPS = 60
        self.TIME_STEP = 1.0 / self.TARGET_FPS
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1300, 700
        
        # Game variables
        self.crashbad = True
        self.max_steps_per_episode = 2000
        self.car_color = 'blue'
        
        # Control variables
        self.pressed_keys = []
        self.time_pressed = {
            'w': 0.0,
            'a': 0.0,
            's': 0.0,
            'd': 0.0
        }
        
        # For whiskers
        # angles, lengths, intercept, normal dot direction 
        angles = [7*np.pi/8, -7*np.pi/8, np.pi/2, -np.pi/2, *[float(x) for x in np.split(np.linspace(-np.pi/5, np.pi/5, 6), 6)]]
        self.rays = np.array([[x, 130, 100, 0] for x in angles])
        
        # World and physics objects, will be initialized in init_track
        self.world = None
        self.car = None
        self.box = None
        self.tracks = []
        self.centerline = []
        self.cpts = []
        self.cp = 0
        
        # Trial data
        self.trial = 0
        self.trials = []
        self.num_trials = 3
    
    def init_track(self, centerline, left, right, checkpoints):
        """Initialize the track, walls, car, and checkpoints."""
        # --- pybox2d world setup ---
        self.world = world(gravity=(0, 0), doSleep=True)
        self.bodies = []
        self.tracks = []
        
        # --- track setup
        outer_track = self.world.CreateBody(shapes=chainShape(vertices=self.rtfm(left)))
        inner_track = self.world.CreateBody(shapes=chainShape(vertices=self.rtfm(right)))
        self.centerline = centerline
        self.spawn = (round(centerline[0][0]/self.PPM), round(centerline[0][1]/self.PPM))
        self.cpts = list(self.rtfm(x) for x in checkpoints)
        
        # Determine track direction (clockwise vs counterclockwise)
        outer_track.fixtures[0].userData = 'outer'
        callback = RayCastClosestCallback()
        i = 0
        while callback.hit == False:  
            self.world.RayCast(callback, (i-10,-10), (i-10,self.SCREEN_HEIGHT/self.PPM))
            i += 3
        
        if callback.fixture.userData != 'outer':
            temp = outer_track
            outer_track = inner_track
            inner_track = temp
            
        self.tracks.append([outer_track, 'white'])
        self.tracks.append([inner_track, 'lightblue'])
        
        self.direction = np.arctan2(centerline[1][1] - centerline[0][1], centerline[1][0] - centerline[0][0])
        
        # --- Create car
        self.car = self.world.CreateDynamicBody(position=self.spawn, angle=self.direction, linearDamping=.3, angularDamping=6)
        self.car_color = 'blue'
        self.box = self.car.CreatePolygonFixture(box=(1, .5), density=1, friction=0.002)
        
        # --- trial spawn locations
        self.trial = 0
        self.trials = [np.random.randint(0, len(self.centerline)-2) for _ in range(self.num_trials)]
    
    def step(self, action=[False, False, False, False]):
        """Advance simulation by one step given the current action."""
        # Default reward if nothing happens
        reward = 0.05
        flags = []
        
        # Handle key actions
        # Action: 0 = w, 1 = a, 2 = s, 3 = d
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
                   
        # Handle movement physics
        fw_speed = (self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity))
        
        for key in self.pressed_keys:
            if key == 'w':
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(120.0, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 's':
                # Braking power is a function of speed, reverse is just fixed force
                if fw_speed > 0:
                    bp = max(min(400.0, abs(fw_speed)*5.0), 100.0)
                else: 
                    bp = 60.0
                
                self.car.ApplyForce(self.car.GetWorldVector(localVector=(-bp, 0.0)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)
            elif key == 'a':
                if self.time_pressed['a'] < 1: 
                    self.time_pressed['a'] += 1  # In effect disabling "time pressed" feature 
                self.car.ApplyTorque(-min(fw_speed*self.time_pressed['a']*.7, 25), True)
                # Hard limit on turning force to prevent oversteer at high speed
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
        # Force in x ensures drifting doesn't penalize speed too badly
        self.car.ApplyForce(-12*self.car.GetWorldVector(localVector=(abs(sideforce/5), sideforce)), self.car.GetWorldPoint(localPoint=(0.0, 0.0)), True)

        # Check checkpoint for collisions
        was_hit = True
        while was_hit:  # To prevent gate skipping at high speed
            callback = myCallback()
            self.world.RayCast(callback, (self.cpts[self.cp][0]), (self.cpts[self.cp][1]))
            if callback.hit:
                reward = 10
                self.cp += 1
                if self.cp >= len(self.cpts): 
                    self.cp = 0
            else: 
                was_hit = False
        
        # Check whiskers
        point1 = self.car.position
        for ray in self.rays:  
            angle = self.car.angle + ray[0]
            d = (ray[1] * np.cos(angle), ray[1] * np.sin(angle))
            point2 = point1 + d
    
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, point1, point2)
            
            if callback.hit:
                ray[2] = np.linalg.norm(point1 - callback.point)
                ray[3] = np.dot((np.cos(self.car.fixtures[0].body.angle), np.sin(self.car.fixtures[0].body.angle)), callback.normal)
            else:
                ray[2] = np.linalg.norm(point1 - point2)
                
        # Check for crashes
        self.car_color = 'blue'
        if self.crashbad:
            for contact in self.car.contacts:
                if self.car.contacts[0].contact.touching:  # AABB collision bug fix
                    self.car_color = 'red'
                    flags.append('crashed')
                
        # Add speed reward
        speed_reward = max(0, self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity)/40) 
        reward += speed_reward
        
        # Advance physics simulation
        self.world.Step(self.TIME_STEP, 2, 2)
        
        return self.get_state(), reward, flags
    
    def reset(self):
        """Reset the car to starting position for a new trial."""
        # Get spawn point index
        spi = self.trials[self.trial]
        self.car.position = self.rtfm(self.centerline[spi])
        self.car.angle = np.arctan2(self.centerline[spi+1][1] - self.centerline[spi][1], 
                                   self.centerline[spi+1][0] - self.centerline[spi][0])
        self.car.angularVelocity = 0.0
        self.car.linearVelocity = (0, 0)
        
        self.cp = spi*5  # 5 comes from track gen checkpoints per point set
        
        # Reset whisker distances, speed, etc. with a step
        self.step()
        
        return self.get_state()
    
    def get_state(self):
        """Get the current state representation for the neural network."""
        state = [
            self.car.GetWorldVector((1,0)).dot(self.car.linearVelocity),  # Car's speed
            *np.split(self.rays[:,2], len(self.rays[:,2])),  # Whisker distances
            *np.split(self.rays[:,3], len(self.rays[:,3]))   # Whisker normals
        ]
        return state
    
    def tfm(self, meters):
        """Transform from meters to pixels for single values and points."""
        if isinstance(meters, (int, float)):
            return meters*self.PPM
        if isinstance(meters, Box2D.b2Vec2):
            return (round(meters[0]*self.PPM), round(meters[1]*self.PPM))
        if isinstance(meters, list):
            rv = []
            for item in meters:
                if isinstance(item, (list, tuple)):  # Handle lists of lists of points
                    rv.append([item[0]*self.PPM, item[1]*self.PPM])
                else:
                    rv.append(item*self.PPM)
            return rv
        return None
        
    def rtfm(self, pix):
        """Reverse transforms a list of points from pixels to meters."""
        if isinstance(pix[0], (int, float)):
            return [pix[0]/self.PPM, pix[1]/self.PPM]
        
        rv = []
        for point in pix:
            rv.append([(point[0]/self.PPM), (point[1]/self.PPM)])
        return rv
