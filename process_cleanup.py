# -*- coding: utf-8 -*-
"""
Improved process cleanup functions for NEAT_drifter.py
"""

import atexit
import signal
import sys
import time

# Global variables to store processes and queues - these will be set in run()
processes = []
q = None
r = None

def cleanup_processes():
    """
    Properly clean up all child processes when the main process exits.
    This function is registered with atexit to ensure it's called on exit.
    """
    global processes, q, r
    
    if processes:
        print("Cleaning up processes before exit...")
        
        # Signal all processes to exit by sending None to the queue
        if q is not None:
            try:
                # Drain the queues first to avoid deadlocks
                while not q.empty():
                    try:
                        q.get_nowait()
                    except:
                        break
                
                # Send termination signals
                for _ in range(len(processes)):
                    q.put(None)
                
                # Close the queue
                q.close()
                q.join_thread()
            except:
                pass  # Queue might be closed already
        
        # Drain and close the results queue
        if r is not None:
            try:
                while not r.empty():
                    try:
                        r.get_nowait()
                    except:
                        break
                r.close()
                r.join_thread()
            except:
                pass
        
        # Give processes a moment to see the termination signal
        time.sleep(0.2)
        
        # Terminate and join all processes
        for process, dc in processes:
            try:
                # Close the direct communication queue
                try:
                    while not dc.empty():
                        dc.get_nowait()
                    dc.close()
                    dc.join_thread()
                except:
                    pass
                
                # Terminate the process
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=0.5)
                    
                    # If process is still alive after terminate and join, kill it
                    if process.is_alive():
                        print(f"Process {process.pid} still alive, killing it...")
                        process.kill()
                        process.join(timeout=0.1)
            except:
                pass  # Process might already be gone
        
        processes.clear()
        print('All processes cleaned up.')
        
        # Ensure Python's internal multiprocessing resources are released
        try:
            import multiprocessing as mp
            mp.current_process()._clean()
        except:
            pass

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up and exiting gracefully."""
    print(f"\nReceived signal {sig}. Cleaning up...")
    cleanup_processes()
    sys.exit(0)

# Register the cleanup function to be called on normal program exit
atexit.register(cleanup_processes)

# Register signal handlers for common termination signals
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination request

# On Windows, we can also handle CTRL_CLOSE_EVENT
if sys.platform == 'win32':
    try:
        signal.signal(signal.CTRL_CLOSE_EVENT, signal_handler)
    except:
        pass  # Some Windows Python builds don't have this