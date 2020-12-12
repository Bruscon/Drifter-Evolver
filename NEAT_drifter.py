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

import ntools


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
    else:
        centerline = [[623, 369], [652, 369], [681, 361], [706, 345], [725, 322], [736, 294], [738, 264], [731, 235], [716, 209], [694, 189], [667, 176], [637, 172], [607, 177], [580, 190], [558, 210], [543, 236], [536, 265], [538, 295], [549, 323], [568, 346], [593, 362], [622, 370]]
        left = [[573, 434], [528, 409], [491, 371], [468, 322], [461, 270], [470, 218], [493, 173], [530, 135], [574, 109], [625, 98], [677, 102], [727, 121], [766, 154], [796, 198], [811, 246], [811, 299], [795, 349], [764, 393], [721, 424], [672, 441], [623, 444]]
        right = [[613, 290], [608, 283], [607, 275], [608, 268], [611, 260], [616, 254], [623, 247], [630, 245], [640, 245], [649, 246], [657, 250], [661, 257], [666, 264], [666, 272], [665, 282], [661, 289], [655, 295], [648, 297], [641, 298], [632, 297], [623, 294]]
        checkpoints = [[(623, 444), (623, 294)], [(635, 443), (625, 294)], [(647, 442), (627, 295)], [(659, 441), (629, 296)], [(672, 441), (632, 297)], [(672, 441), (632, 297)], [(684, 436), (634, 297)], [(696, 432), (636, 297)], [(708, 428), (638, 297)], [(721, 424), (641, 298)], \
                       [(721, 424), (641, 298)], [(731, 416), (642, 297)], [(742, 408), (644, 297)], [(753, 400), (646, 297)], [(764, 393), (648, 297)], [(764, 393), (648, 297)], [(771, 382), (649, 296)], [(779, 371), (651, 296)], [(787, 360), (653, 295)], [(795, 349), (655, 295)], \
                        [(795, 349), (655, 295)], [(799, 336), (656, 293)], [(803, 324), (658, 292)], [(807, 311), (659, 290)], [(811, 299), (661, 289)], [(811, 299), (661, 289)], [(811, 285), (662, 287)], [(811, 272), (663, 285)], [(811, 259), (664, 283)], [(811, 246), (665, 282)], \
                        [(811, 246), (665, 282)], [(807, 234), (665, 279)], [(803, 222), (665, 277)], [(799, 210), (665, 274)], [(796, 198), (666, 272)], [(796, 198), (666, 272)], [(788, 187), (666, 270)], [(781, 176), (666, 268)], [(773, 165), (666, 266)], [(766, 154), (666, 264)], \
                        [(766, 154), (666, 264)], [(756, 145), (664, 262)], [(746, 137), (663, 260)], [(736, 129), (662, 258)], [(727, 121), (661, 257)], [(727, 121), (661, 257)], [(714, 116), (660, 255)], [(702, 111), (659, 253)], [(689, 106), (658, 251)], [(677, 102), (657, 250)], \
                        [(677, 102), (657, 250)], [(664, 101), (655, 249)], [(651, 100), (653, 248)], [(638, 99), (651, 247)], [(625, 98), (649, 246)], [(625, 98), (649, 246)], [(612, 100), (646, 245)], [(599, 103), (644, 245)], [(586, 106), (642, 245)], [(574, 109), (640, 245)], \
                        [(574, 109), (640, 245)], [(563, 115), (637, 245)], [(552, 122), (635, 245)], [(541, 128), (632, 245)], [(530, 135), (630, 245)], [(530, 135), (630, 245)], [(520, 144), (628, 245)], [(511, 154), (626, 246)], [(502, 163), (624, 246)], [(493, 173), (623, 247)], \
                        [(493, 173), (623, 247)], [(487, 184), (621, 248)], [(481, 195), (619, 250)], [(475, 206), (617, 252)], [(470, 218), (616, 254)], [(470, 218), (616, 254)], [(467, 231), (614, 255)], [(465, 244), (613, 257)], [(463, 257), (612, 258)], [(461, 270), (611, 260)], \
                        [(461, 270), (611, 260)], [(462, 283), (610, 262)], [(464, 296), (609, 264)], [(466, 309), (608, 266)], [(468, 322), (608, 268)], [(468, 322), (608, 268)], [(473, 334), (607, 269)], [(479, 346), (607, 271)], [(485, 358), (607, 273)], [(491, 371), (607, 275)], \
                        [(491, 371), (607, 275)], [(500, 380), (607, 277)], [(509, 390), (607, 279)], [(518, 399), (607, 281)], [(528, 409), (608, 283)], [(528, 409), (608, 283)], [(539, 415), (609, 284)], [(550, 421), (610, 286)], [(561, 427), (611, 288)], [(573, 434), (613, 290)], \
                        [(573, 434), (613, 290)], [(585, 436), (615, 291)], [(598, 439), (618, 292)], [(610, 441), (620, 293)], [(623, 444), (623, 294)]]
        rv = (centerline,left,right,checkpoints)
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
            
    num_workers = mp.cpu_count()
    processes, drifters = [], []
    q = mp.Queue() #tasks queue, a genome will go in here
    r = mp.Queue() #results queue, a fitness score will come out of here
    
    for i in range(num_workers):
        drifters.append( MPDrifter( q, r, rv, config ) )
        processes.append( mp.Process(target=drifters[-1].mp, args=() ) )
        processes[-1].start()
        
    pe = neat.ParallelEvaluator(q, r)    
    
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
        flags = []
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