[NEAT]
fitness_criterion     = max
fitness_threshold     = 3.9 
no_fitness_termination = True
pop_size              = 300
reset_on_extinction   = False

[DefaultGenome]
# node activation options
activation_default      = random
activation_mutate_rate  = 0.02
activation_options      = sigmoid relu log exp abs tanh

# node aggregation options
aggregation_default     = random
aggregation_mutate_rate = 0.02
aggregation_options     = sum product min max mean median maxabs

# node bias options
bias_init_mean          = 0.0
bias_init_stdev         = 1.0
bias_max_value          = 30.0
bias_min_value          = -30.0
bias_mutate_power       = 0.2
bias_mutate_rate        = 0.01
bias_replace_rate       = 0.01

# genome compatibility options
#compatibility_threshold = #IDK what this should be
compatibility_disjoint_coefficient = 1.0
compatibility_weight_coefficient   = 0.5

# connection add/remove rates
conn_add_prob           = 0.02
conn_delete_prob        = 0.01

# connection enable options
enabled_default         = True
enabled_mutate_rate     = 0.02

feed_forward            = False
initial_connection      = partial_direct .2

# node add/remove rates
node_add_prob           = 0.03
node_delete_prob        = 0.02

# network parameters
num_hidden              = 10
num_inputs              = 7
num_outputs             = 4

# node response options
response_init_mean      = 1.0
response_init_stdev     = 0.0
response_max_value      = 30.0
response_min_value      = -30.0
response_mutate_power   = 1.0
response_mutate_rate    = 0.03
response_replace_rate   = 0.003

# connection weight options
weight_init_mean        = 0.0
weight_init_stdev       = 1.0
weight_max_value        = 30
weight_min_value        = -30
weight_mutate_power     = 0.3
weight_mutate_rate      = 0.07
weight_replace_rate     = 0.03

[DefaultSpeciesSet]
compatibility_threshold = 3.0

[DefaultStagnation]
species_fitness_func = mean
max_stagnation       = 20
species_elitism      = 6

[DefaultReproduction]
elitism            = 1
survival_threshold = 0.30