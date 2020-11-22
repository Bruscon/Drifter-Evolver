# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 21:29:57 2020

@author: Nick Brusco
"""
import tkinter as tk


class Dgui:
    name = "Drifter GUI"
    description = "Puts all your settings in a seperate tkinter window."


    def __init__ (self, config):
        
        self.fields = ['Population']
        ''', 'Activation Mutate Rate', 'Aggregation Mutate Rate', 
                       'bias_max_value', 'bias_min_value', 'bias_mutate_power','bias_mutate_rate',
                       'bias_replace_rate']
        '''
        self.new_config = config.pop_size
        
        self.root = tk.Tk()
        ents = self.makeform(self.fields)
        self.root.bind('<Return>', (lambda event, e=ents: self.fetch(e)))   
        b1 = tk.Button(self.root, text='Show',
                      command=(lambda e=ents: self.fetch(e)))
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.root, text='Quit', command=self.root.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def fetch(self, entries):
        for entry in entries:
            field = entry[0]
            text  = entry[1].get()
            print('%s: "%s"' % (field, text)) 
        self.new_config = int(text)
    
    def makeform(self, fields):
        entries = []
        for field in fields:
            row = tk.Frame(self.root)
            lab = tk.Label(row, width=25, text=field, anchor='w')
            ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            entries.append((field, ent))
        return entries
    
    def step(self, config):
        config.pop_size = self.new_config
        self.root.update()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    