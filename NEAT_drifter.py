# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 10:34:02 2020

@author: Nick Brusco
"""
import os
import sys
import multiprocessing
import neat
from NEAT_drifter_class import Drifter
from mpdrifter import MPDrifter
import Dgui
import TrackGen

import ntools


def eval_genome(genome, config, track):
    
    genome.fitness = 0
    nn = neat.nn.RecurrentNetwork.create(genome, config)
    
    mpdft = MPDrifter()
    mpdft.init_track(*track)
    
    done = False
    fitness = 0
    for timestep in range(1, mpdft.max_steps_per_episode):

        #run inputs through neural net
        outputs = nn.activate(mpdft.get_state())
        
        #convert probabilities to binary key press outputs
        keys = []
        for key in outputs:
            keys.append(key > 0)
        
        #apply outputs to game 
        state, reward, flags = mpdft.step(keys)
        
        for flag in flags:
            if flag == 'crashed':
                reward /= 2
                done = True
                break
            
            
        fitness += reward

        if done:
            break
    
    return fitness


def run(config_path):
    #get command line arguments
    args = sys.argv
    
    dft = Drifter()

    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    
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
        dft.init_track(*rv)
    
    #if we're not just manually driving the car:
    if 'm' not in args:
        # Create the population, which is the top-level object for a NEAT run.
        p = neat.Population(config)
        
        # Add a stdout reporter to show progress in the terminal.
        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)
        p.add_reporter(neat.Checkpointer(100,99999999)) #Saves current state every 25 generations
    
    if 'm' in args:
        while(1):
            dft.mstep()
        
        
    pe = neat.ParallelEvaluator(multiprocessing.cpu_count(), eval_genome, track = rv)    
    
    while(1):
        # Run a generation
        dft.graphics = False
        
        winner = p.run(pe.evaluate, 1)
        #winner = p.run(eval_genomes, 1)
        
        winner_net = neat.nn.RecurrentNetwork.create(winner, config)
        
        
        #the rest of this loop is to replay the winner
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


if __name__ == '__main__':

    

    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'NEAT_config.py')
    print(os.path)
    run(config_path)