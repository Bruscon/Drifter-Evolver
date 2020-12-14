# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 10:34:02 2020

@author: Nick Brusco
"""
import os
import sys
import multiprocessing as mp
import neat
from NEAT_drifter_class import Drifter
from mpdrifter import MPDrifter
import Dgui
import TrackGen
import pickle
import random
import atexit

import ntools


@atexit.register
def kill_subprocesses():
    print("killing all processes and exiting...")
    global processes, q
    for process, _ in processes:
        q.put(None)
    for process, _ in processes:
        process.kill()
        process.terminate()
        process.join(0)
    print('Complete.')
    
    
def send_to_subprocesses(command):
    global processes, q
    for _, dc in processes:       #send a message to each subprocess individually
        dc.put(command)
        
    for _, _ in processes:       #tell the subprocesses to read their direct coms
        q.put('read dc')
        
    for _, dc in processes:             #Wait for all subprocesses to finish
        dc.join()


def run(config_path):
    # --- get command line arguments
    args = sys.argv
    
    dft = Drifter()

    # --- Load configuration.
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
    
    if 't' in args:         #if were using a premade track
        with open('tracks/Drifty.track','rb') as dbfile :
            db = pickle.load(dbfile)
        rv = (db['points'],db['lbound'],db['rbound'],db['checkpoints'])
        dft.init_track(*rv)
    else:
        tg = TrackGen.TrackGen(dft)
        rv = None
        while(rv == None):
            rv = tg.step()
        dft.init_track(*rv)

    if 'm' in args:             #if were driving manually
        while(1):
            dft.mstep()

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)
    
    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(100,99999999)) #Saves current state every 100 generations
    '''The checkpoint files keep growing in size, after a few thousand generations 
    theyre 50+ Mb. No idea why, definitely fix this '''
            
    global processes, q
    num_workers = max(2, mp.cpu_count()-2)
    processes, drifters = [], []
    q = mp.Queue() #tasks queue, a genome will go in here
    r = mp.Queue() #results queue, a fitness score will come out of here
    
    for i in range(num_workers):
        dc = mp.JoinableQueue() #direct communication queue to this process only
        drifters.append( MPDrifter( q, r, dc, rv, dft.trials, config ) )
        processes.append( ( mp.Process( target=drifters[-1].mp, args=() ), dc) )
        processes[-1][0].start()
        
    pe = neat.ParallelEvaluator(q, r)    
    p.start_gen(pe.start_evaluate, 1) #start training
    
    # --- mainloop
    while(1):
        
        # --- handle user commands
        command = dft.get_commands()            #see if user typed any commands
        if command != []:                       #if they did:
            send_to_subprocesses(command)
        
        # --- Run a generation
        winner = p.run(pe.finish_evaluate, 1) #get results of last training session
        
        # --- change the start locations for only one of the next generation
        dft.trials[random.randint(0,len(dft.trials)-1)] = random.randint(0, len(dft.centerline)-2)
        send_to_subprocesses( ('start points', dft.trials) ) #update the suprocesses as well
        
        # --- start nextgeneration so it can train while we display
        p.start_gen(pe.start_evaluate, 1) 
        
        winner_net = neat.nn.RecurrentNetwork.create(winner, config)
        
        
        # --- replay winner
        dft.trial = 0
        for trl in dft.trials:
            dft.reset()
            dft.trial += 1
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
    run(config_path)