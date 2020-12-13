#!/usr/bin/env python3 
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 11:42:13 2020

@author: Nick
"""

import multiprocessing as mp
import time
import os
import itertools

def count_to(target, target2):
    target *= 10000000 #ten million
    i=0
    while i < target:
        i+=1
    print('done')
    print(f'second arg is {target2}') #to demonstrate multiple arguments
    return os.getpid()

if __name__ == '__main__':
    
    ''' Comparison using Process '''
    starttime = time.time()
    
    jobs = []
    
    for i in range(round(mp.cpu_count()/2)):
        a = mp.Process(target=count_to, kwargs={'target' : 1, 'target2' : 2})
        jobs.append(a)
        
    for job in jobs:
        job.start()

    jobs[-1].join()

    mpt = time.time()-starttime
    print(mpt, ' is the multiprocessing time')
    
    
    starttime = time.time()
    
    i=0
    while( i<round(mp.cpu_count()/2)):
        count_to(1,3)
        i+=1
    
    spt = time.time()-starttime
    print(spt, 'is the standard processing time')
    
    print(spt/mpt, " times faster with multiprocessing")
   
    
    ''' Comparison using Pool '''
    starttime = time.time()
    
    pool = mp.Pool(processes = round(mp.cpu_count()/2))
    print(pool.starmap(count_to, zip([5]*5, itertools.repeat(4))   )) #starmap for multiple arguments

    mpt = time.time()-starttime
    print(mpt, ' is the pool multiprocessing time')



    starttime = time.time()
    
    i=0
    while( i<round(mp.cpu_count()/2)):
        count_to(5,4)
        i+=1
    
    spt = time.time()-starttime
    print(spt, 'is the standard processing time')
    
    print(spt/mpt, " times faster with multiprocessing")