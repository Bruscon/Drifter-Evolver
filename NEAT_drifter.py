# -*- coding: utf-8 -*-
"""
Main NEAT_drifter application file with improved process cleanup.

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
import ntools

# Import process cleanup utilities
from process_cleanup import processes, q, cleanup_processes

def send_to_subprocesses(command):
    """Send a command to all subprocesses."""
    global processes, q
    for _, dc in processes:       # Send a message to each subprocess individually
        dc.put(command)
        
    for _, _ in processes:       # Tell the subprocesses to read their direct coms
        q.put('read dc')
        
    for _, dc in processes:      # Wait for all subprocesses to finish
        dc.join()


def run(config_path):
    """Main application loop."""
    # --- Get command line arguments
    args = sys.argv
    
    dft = Drifter()

    # --- Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    
    # Initialize track or use track generator
    if 't' in args:         # If we're using a premade track
        with open('tracks/bendy.track', 'rb') as dbfile:
            db = pickle.load(dbfile)
        rv = (db['points'], db['lbound'], db['rbound'], db['checkpoints'])
        dft.init_track(*rv)
    else:
        tg = TrackGen.TrackGen(dft)
        rv = None
        while rv is None:
            rv = tg.step()
        dft.init_track(*rv)

    if 'm' in args:             # If we're driving manually
        while True:
            dft.mstep()

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)
    
    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(100, 99999999))  # Saves current state every 100 generations
            
    # Set up multiprocessing
    num_workers = max(2, mp.cpu_count() - 2)
    global processes, q
    processes.clear()  # Clear any existing processes 
    drifters = []
    q = mp.Queue()  # Tasks queue
    r = mp.Queue()  # Results queue, a fitness score will come out of here
    
    # Create worker processes
    for i in range(num_workers):
        dc = mp.JoinableQueue()  # Direct communication queue to this process only
        drifters.append(MPDrifter(q, r, dc, rv, dft.trials, config))
        # Set daemon=True to ensure processes exit when the main process exits
        proc = mp.Process(target=drifters[-1].mp, args=(), daemon=True)
        processes.append((proc, dc))
        proc.start()
        
    pe = neat.ParallelEvaluator(q, r)    
    p.start_gen(pe.start_evaluate, 1)  # Start training
    
    try:
        # --- Main loop
        while True:
            # --- Handle user commands
            command = dft.get_commands()            # See if user typed any commands
            if command != []:                       # If they did:
                send_to_subprocesses(command)
            
            # --- Run a generation
            winner = p.run(pe.finish_evaluate, 1)  # Get results of last training session
            
            # --- Change the start locations for only one of the next generation
            dft.trials[random.randint(0, len(dft.trials) - 1)] = random.randint(0, len(dft.centerline) - 2)
            send_to_subprocesses(('start points', dft.trials))  # Update the suprocesses as well
            
            # --- Start next generation so it can train while we display
            p.start_gen(pe.start_evaluate, 1) 
            
            winner_net = neat.nn.RecurrentNetwork.create(winner, config)
            
            dft.step()
            if not dft.graphics:
                continue
            
            # --- Replay winner
            dft.trial = 0
            for trl in dft.trials:
                dft.reset()
                dft.trial += 1
                done = False
                for timestep in range(1, dft.max_steps_per_episode):
                    # Run inputs through neural net
                    outputs = winner_net.activate(dft.get_state())
                    
                    # Convert probabilities to binary key press outputs
                    keys = []
                    for key in outputs:
                        keys.append(key > 0)
                    
                    # Apply outputs to game 
                    state, reward, flags = dft.step(keys)
                    
                    for flag in flags:
                        if flag == 'crashed':
                            done = True
                            break    
                    if done:
                        break
    except KeyboardInterrupt:
        print("\nInterrupted by user. Cleaning up...")
        cleanup_processes()
    except Exception as e:
        print(f"\nError occurred: {e}. Cleaning up...")
        cleanup_processes()
        raise


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'NEAT_config.py')
    
    try:
        run(config_path)
    finally:
        # This ensures cleanup happens even if there's an unhandled exception
        # Though atexit should handle this anyway, it's a good backup
        cleanup_processes()