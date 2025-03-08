# -*- coding: utf-8 -*-
"""
Modified MPDrifter class that inherits from BaseDrifter.

@author: Nick Brusco
"""

import os
import sys
import numpy as np
import random
import neat

from BaseDrifter import BaseDrifter, myCallback
from Box2D.examples.raycast import RayCastClosestCallback

class MPDrifter(BaseDrifter):
    """
    Multiprocessing-compatible version of Drifter.
    Inherits shared functionality from BaseDrifter.
    """
    
    name = "Multiprocessing Drifter"
    description = "The multiprocessing-compatible version of Drifter"
    
    def __init__(self, q, r, dc, track, trials, config):
        # Initialize the base class
        super().__init__()
        
        # Setup multiprocessing
        self.q = q      # Queue for unsolved genomes
        self.r = r      # Queue for solved fitness scores
        self.dc = dc    # Queue for direct comms to this subprocess
        
        # Configuration
        self.track = track
        self.config = config
        self.trials = trials
        self.pid = None  # Process ID, set in mp() method
    
    def mp(self):
        """
        Multiprocess entry point. This function runs infinitely as a separate process
        until terminated.
        """
        self.init_track(*self.track)  # Initialize the track in the subprocess
        self.pid = os.getpid()
        
        while True:
            fromq = self.q.get()  # Take from the queue, or wait if none are available
            
            if fromq == None:  # If the genome is None, kill the process
                sys.exit()
                return 0
            if fromq == 'read dc':  # Instruction to process direct communication
                self.process_command()
                continue
                
            # Process the genome
            genome_id, genome = fromq
            nn = neat.nn.RecurrentNetwork.create(genome, self.config)
            genome.fitness = 0
            fitness = 0
            
            # Run the genome through trials
            self.trial = 0
            for trl in self.trials:
                self.reset()
                self.trial += 1
                done = False      
                flags = []
                for timestep in range(1, self.max_steps_per_episode):
                    
                    # Run inputs through neural net
                    outputs = nn.activate(self.get_state())
                    
                    # Convert probabilities to binary key press outputs
                    keys = []
                    for key in outputs:
                        keys.append(key > 0)
                    
                    # Apply outputs to game 
                    state, reward, flags = self.step(keys)
                    
                    for flag in flags:
                        if flag == 'crashed':
                            done = True
                            break
                        
                    fitness += reward
            
                    if done:
                        break
            
            # Store fitness result and signal completion
            genome.fitness = fitness
            self.r.put((genome_id, genome))
            
    def process_command(self):
        """Process commands sent via direct communication."""
        arg = self.dc.get()
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

        self.dc.task_done()  # Allow main process to continue
            
    def new_track(self, args):
        """Update track with new data."""
        self.init_track(*args)
    
    def new_runtime(self, arg):
        """Update maximum steps per episode."""
        self.max_steps_per_episode = int(arg[0])
        
    def new_config(self, args):
        """Update NEAT configuration."""
        # Not implemented yet
        pass 
    
    def set_crashbad(self, args):
        """Set whether crashing ends the simulation."""
        if args[0].lower() in ['1', 'true', 't', 'yes']:
            self.crashbad = True
        elif args[0].lower() in ['0', 'false', 'f', 'no']:
            self.crashbad = False
        else:
            raise Exception(f'Received a bad crashbad argument: {args[0]}')
        
    def start_points(self, arg):
        """Update starting points for trials."""
        self.trials = arg[0]