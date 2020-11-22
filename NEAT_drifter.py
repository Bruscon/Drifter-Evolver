# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 10:34:02 2020

@author: Nick Brusco
"""

#from __future__ import print_function
import os
import neat
import visualize
from NEAT_drifter_class import *
import Dgui
import TrackGen

def eval_genomes(genomes, config):
    
    
    for genome_id, genome in genomes:
        genome.fitness = 0
        nn = neat.nn.RecurrentNetwork.create(genome, config)
        
        dft.reset()
        
        done = False
        fitness = 0
        for timestep in range(1, dft.max_steps_per_episode):
            
            #data to display on screen needs to be passed to pygame
            if dft.graphics:
                dft.stats = { 'pop': int(str(p.species.indexer)[6:-1])-1, #number of species
                             'gen': p.generation
                         }
        
                gui.step(config)

            #run inputs through neural net
            outputs = nn.activate(dft.get_state())
            
            #convert probabilities to binary key press outputs
            keys = []
            for key in outputs:
                keys.append(key > 0)
            
            #apply outputs to game 
            state, reward, flags = dft.step(keys)
            
            for flag in flags:
                if flag == 'quit':
                    running = False
                if flag == 'crashed':
                    reward /= 3
                    done = True
                    break
                
                
            fitness += reward

            if done:
                break
        
        genome.fitness = fitness

#get command line arguments
args = sys.argv

dft = Drifter()

local_dir = os.path.dirname(__file__)
config_file = os.path.join(local_dir, 'NEAT_config.py')

# Load configuration.
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_file)

#Initialize the gui with initial NEAT config 
#gui = Dgui.Dgui(config)
'''
Notes on where you left off:
    editing the population size on the config does not change the population size
    because the population is only made once. I think it will work for things that edit
    params in the NN because the NN is created each time a creature is run.
    To change population size you probably need to save your population, delete it,
    make a new one of the correct size and populate it with the correct number of the
    old creatures.
'''

#if were not using a premade track
if 't' not in args:
    tg = TrackGen.TrackGen(dft)
    rv = None
    while(rv == None):
        rv = tg.step()

    centerline, left, right, checkpoints = rv
    dft.init_track(left, right, centerline, checkpoints)


#if we're not just manuatlly driving the car:
if 'm' not in args:
    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)
    
    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(25)) #Saves current state every 25 generations

if 'm' in args:
    while(1):
        dft.mstep()
    

while(1):
    # Run a generation
    dft.graphics = False
    winner = p.run(eval_genomes, 1)
    
    winner_net = neat.nn.RecurrentNetwork.create(winner, config)
    
    dft.graphics = True
    dft.reset()
    done = False
    for timestep in range(1, dft.max_steps_per_episode):
            
            #run inputs through neural net
            outputs = winner_net.activate(dft.get_state())
            
            #convert probabilities to binary key press outputs
            keys = []
            for key in outputs:
                keys.append(key > 0)
            
            #apply outputs to game 
            state, reward, flags = dft.step(keys)
            
            for flag in flags:
                if flag == 'quit':
                    running = False
                if flag == 'crashed':
                    done = True
                    break

            if done:
                break

    '''
    Visualizer doesnt work. Big deal.
    
    node_names = {-1:'speed', -2: 'heading', -3:'whisker', -4:'whisker', -5:'whisker', -6:'whisker', -7:'whisker', 0:'w',1:'a',2:'s',3:'d'}
    visualize.draw_net(config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)
    '''