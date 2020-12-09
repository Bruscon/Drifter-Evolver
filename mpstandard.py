# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 11:06:21 2020

@author: Nick Brusco
"""
import multiprocessing as mp
import time

class runner:
    def __init__(self, name, q, r, e):
        self.name = name
        self.q = q
        self.r = r
        self.e = e #event. use as if it were named "is_done_processing"
        
    def f(self):
        while(1):
            fromq = self.q.get()
            self.e.clear()
            if fromq == None: #to kill the process
                break
            for i in range(10**7): pass #just count really high to spin the wheels
            self.r.put(fromq*2)
            self.e.set()

if __name__ == '__main__':
    q = mp.Queue() #tasks queue, a genome will go in here
    r = mp.Queue() #results queue, a fitness score will come out of here
    
    
    for num_processes in range( 1, mp.cpu_count()*2 ) : #test to find the number of processes for fastest execution
        
        processes = []
        runners = []
        events = [] 
        
        for i in range(num_processes):
            e = mp.Event()
            events.append( e )
            runners.append( runner(i, q, r, e) )
            processes.append( mp.Process(target=runners[-1].f, args=() ) )
            processes[-1].start()
            '''one slight bug, all these processes still exist even though I kill
            them later in the program. Open task manager after the program completes
            to see what i mean'''
        
        for j in range(10):
            q.put(j)
        
        _start = time.time()
        
        while not q.empty() : pass
        for event in events:
            event.set() #blocks (hopefully without polling?) until event is True
        
        #print(r.get(), r.get(), r.get(), r.get(), r.get(), r.get(), r.get(), r.get(), r.get(), r.get())
        print(f'took {round(time.time()-_start,2)} seconds with {num_processes} processes')
        
        #kill all the processes
        for j in range(num_processes):
            q.put(None)
        
        
        for process in processes:
            process.terminate()
            process.join(2)
            del process
           
            
    breakpoint()