"""
Runs evaluation functions in parallel subprocesses
in order to evaluate multiple genomes at once.
"""
import multiprocessing as mp
import itertools

class ParallelEvaluator(object):
    def __init__(self, q, r, timeout=None):
        """
        eval_function should take one argument, a tuple of
        (genome object, config object), and return
        a single float (the genome's fitness).
        """
        self.timeout = timeout
        self.q = q
        self.r = r


    def __del__(self):
        pass

    def evaluate(self, genomes, config):
        
        for key, value in genomes.items():
            self.q.put((key,value))
            
        for i in range(len(genomes)):
            key, genome = self.r.get()
            genomes[key].fitness = genome.fitness
            
