# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 19:40:02 2020

@author: Nick Brusco
"""
from Box2D import (b2World, b2Vec2, b2Vec2_zero)
from Box2D.examples.framework import (Framework, Keys, main, FrameworkBase)
from Box2D import (b2EdgeShape, b2FixtureDef, b2PolygonShape, b2_dynamicBody,
                   b2_kinematicBody, b2_staticBody, b2ChainShape)

    
    
class Drifter(Framework):
    name = "Drifter"
    description = "WASD to move and drift your car"
    speed = 3  # platform speed

    def __init__(self):
        super(Drifter, self).__init__()


        # The ground
        ground = self.world.CreateBody(
            shapes=b2ChainShape(vertices=[(-20, 0), (20, 0),(20,20),(-20,20)])
        )

        # The attachment
        self.car = self.world.CreateDynamicBody(
            position=(0, 3),
            fixtures=b2FixtureDef(
                shape=b2PolygonShape(box=(1, 2)), density=2.0),
        )
        
        print(dir(self.world.gravity.Set(0,0)))
        print(self.world.gravity.y)


    def Keyboard(self, key):
        if key == Keys.K_d:
            self.platform.type = b2_dynamicBody
        elif key == Keys.K_s:
            self.platform.type = b2_staticBody
        elif key == Keys.K_k:
            self.platform.type = b2_kinematicBody
            self.platform.linearVelocity = (-self.speed, 0)
            self.platform.angularVelocity = 0

    def Step(self, settings):
        super(Drifter, self).Step(settings)

        

if __name__ == "__main__":
    main(Drifter)