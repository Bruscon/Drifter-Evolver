# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 11:06:21 2020

@author: Nick Brusco

This works almost perfectly and is to be used as a template for future multiprocessessing.
The only issue is that you cant delete everything with cleanup() and then 
make 12 new processes with run(). No idea why it fails. Its not needed for Drifter anyway. 
"""
import multiprocessing as mp
import time
import os, gc, sys

class runner:
    def __init__(self, name, q, r, dc):
        self.name = name
        self.q = q
        self.r = r
        self.dc = dc
        self.x = 7
        
    def f(self):
        self.pid = os.getpid()
        while(1):
            fromq = self.q.get()
            #print(f"process {self.pid} as worker {self.name} recieved {fromq}")
            
            if fromq == 'read dc': 
                self.process_command(self.dc.get())
                continue
            if fromq == None: #kill process if we recieve None
                sys.exit()
                return None
            
            for i in range(10**self.x): pass #count to ten million to spin the wheels
            self.r.put(fromq*2)
            #print(f"process {self.pid} as worker {self.name} finished")
            
    def process_command(self, instruction):
        print(f'process {self.pid} recieved message {instruction}')
        self.dc.task_done()
            
            
def cleanup():
    #not sure how much of this is really necessary but i REALLY wanted
    #to make sure these processes were dead
    
    while q.empty(): #keep adding None's to the queue until there are no more processes to eat them
        q.put(None)
        time.sleep(.01)
    
    global processes, runners
    
    for process, _ in processes:
        process.kill()
        process.terminate()
        process.join(0)
        
    gc.collect()
    

def test(num):
    '''argument is how many times to count to ten million'''
    for j in range(num):
        q.put(j)
    
    _start = time.time()
    
    summ=0
    for i in range(num):
        summ +=r.get()
    print(f'checksum = {summ}')
    print(f'took {round(time.time()-_start,2)} seconds')
    
    return summ


def run(num_processes):
    global q,r 
    global processes, runners
    
    for i in range(num_processes):
        dc = mp.JoinableQueue() #direct communication queue to this process only
        runners.append( runner(i, q, r, dc ))
        processes.append( ( mp.Process(target=runners[-1].f, args=() ) , dc))
        processes[-1][0].start()
    
    if not test(40) == test(40): print('ALERT! CHECKSUMS NOT EQUAL!'*4)
    

if __name__ == '__main__':
    
    global q,r, processes, runners
    
    processes, runners = [], []
    q = mp.Queue() #tasks queue, a genome will go in here
    r = mp.Queue() #results queue, a fitness score will come out of here

    
    run(mp.cpu_count())
    test(40)
    
    _start = time.time()
    
    for process, dc in processes:       #send a message to each subprocess individually
        dc.put('execute order 69')
        
    for process, dc in processes:       #tell the subprocesses to read their direct coms
        q.put('read dc')
        
    for _, dc in processes:             #recieve confirmation messages from all subprocesses
        dc.join()
        
    print(f'took {round(time.time()-_start,2)} seconds to send messages to 12 subprocesses')
        
    test(40)
    
    breakpoint()

        