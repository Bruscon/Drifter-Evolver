# -*- coding: utf-8 -*-
"""
Process cleanup functions for NEAT_drifter.py
"""

import atexit
import signal
import sys

# Global variables to store processes and queues - these will be set in run()
processes = []
q = None

def cleanup_processes():
    """
    Properly clean up all child processes when the main process exits.
    This function is registered with atexit to ensure it's called on exit.
    """
    global processes, q
    
    if processes:
        print("Cleaning up processes before exit...")
        
        # Signal all processes to exit by sending None to the queue
        if q is not None:
            for _ in range(len(processes)):
                try:
                    q.put(None)
                except:
                    pass  # Queue might be closed already
        
        # Terminate and join all processes
        for process, _ in processes:
            try:
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