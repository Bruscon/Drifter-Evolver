# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 19:40:02 2020

@author: Nick Brusco
"""
from Box2D import (b2World, b2Vec2, b2Vec2_zero)
from Box2D.examples.framework import (Framework, Keys, main, FrameworkBase)
from Box2D import (b2EdgeShape, b2FixtureDef, b2PolygonShape, b2_dynamicBody,
                   b2_kinematicBody, b2_staticBody, b2ChainShape)
from Box2D.b2 import vec2
import numpy

    
    
class Drifter(Framework):
    name = "Drifter"
    description = "WASD to move and drift your car"
    pressed_keys = []
    time_pressed = {
        'w' : 0.0,
        'a' : 0.0,
        's' : 0.0,
        'd' : 0.0
        }

    def __init__(self):
        super(Drifter, self).__init__()

        # --- constants ---
        PPM = 20.0  # pixels per meter
        TARGET_FPS = 60
        TIME_STEP = 1.0 / TARGET_FPS
        SCREEN_WIDTH, SCREEN_HEIGHT = 1500, 900
        bodies = []

        #track setup
        outer_track = self.world.CreateBody(shapes=b2ChainShape(vertices=[(3,3), (int(SCREEN_WIDTH/PPM)-3, 3),(int(SCREEN_WIDTH/PPM)-3,int(SCREEN_HEIGHT/PPM)-3),(3,int(SCREEN_HEIGHT/PPM)-3)]))
        bodies.append([outer_track,'white'])
        inner_track = self.world.CreateBody(shapes=b2ChainShape(vertices=[(17,int(SCREEN_HEIGHT/PPM)-17),(int(SCREEN_WIDTH/PPM)-17,int(SCREEN_HEIGHT/PPM)-17),(int(SCREEN_WIDTH/PPM)-17, 17),(17,17)]))
        bodies.append([inner_track,'gray'])
        
        # Create car
        self.car = self.world.CreateDynamicBody(position=(10, 15), angle=numpy.pi/2, linearDamping=.4, angularDamping = 6, gravityScale=0.0)
        bodies.append([self.car,'red'])
        self.box = self.car.CreatePolygonFixture(box=(1, .5), density=4, friction=0.2)
        

    def Keyboard(self, key):
    
        if key == Keys.K_w and 'w' not in self.pressed_keys:
            self.pressed_keys.append('w')
        if key == Keys.K_a and 'a' not in self.pressed_keys:
            self.pressed_keys.append('a')
        if key == Keys.K_s and 's' not in self.pressed_keys:
            self.pressed_keys.append('s')
        if key == Keys.K_d and 'd' not in self.pressed_keys:
            self.pressed_keys.append('d')
            
    def KeyboardUp(self, key):
        
        if key == Keys.K_w and 'w' in self.pressed_keys:
            self.pressed_keys.remove('w')
        if key == Keys.K_a and 'a' in self.pressed_keys:
            self.pressed_keys.remove('a')
            self.time_pressed['a'] = 0
        if key == Keys.K_s and 's' in self.pressed_keys:
            self.pressed_keys.remove('s')
        if key == Keys.K_d and 'd' in self.pressed_keys:
            self.pressed_keys.remove('d')
            self.time_pressed['d'] = 0

    def Step(self, settings):
        super(Drifter, self).Step(settings)
        
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
        sideforce = numpy.sign(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity))*min(6,abs(self.car.GetWorldVector((1,0)).cross(self.car.linearVelocity)))
        self.car.ApplyForce(-60*self.car.GetWorldVector(localVector=(0,sideforce)), self.car.GetWorldPoint(localPoint=(0.0,0.0)),True)

        

if __name__ == "__main__":
    main(Drifter)