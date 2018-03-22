################################################################################
#
# RUFAS: Ruminant Farm Systems Model
#
# animal.py - 
#
# Authors: Kass Chupongstimun
#          Jit Patil
#
################################################################################

from math import pow

from RUFAS.routines.animal import ration

#------------------------------------------------------------------------------
# Function: daily_animal_routine
# 
#------------------------------------------------------------------------------
def daily_animal_routine(animal, feed, weather, time):
	
	if animal.user_input_ration:
		# Do something
		pass
	else:
		animal.formulate_optimized_ration(feed)

#------------------------------------------------------------------------------
# Function: daily_animal_routine
# 
#------------------------------------------------------------------------------
def daily_animal_update(animal, weather, time):
	pass

#------------------------------------------------------------------------------
# Class: animal
# 
#------------------------------------------------------------------------------
class Animal():

	def __init__(self, data):

		self.housing = data['housing']
		self.user_input_ration = data['ration']['user_input']

		#
		# ARE THESE DIRECT INPUTS OR INTERMEDIATES??????
		# Probably intermediates...
		#
		self.parity = 0.0
		self.WIM = 0.0
		self.AMF = 0.0
		self.BWR = 0.0
		self.base_NED = 0.0

		self.ration = {}

	#------------------------------------------------------------------------------
	# Function: formulate_optimized_ration
	# 
	#------------------------------------------------------------------------------
	def formulate_optimized_ration(self, farm_feed, purchased_feed):
		
		feed = {**farm_feed, **purchased_feed}	# merge feed from farm and purchased

		nutrients_list = ['FI', 'RV', 'NE', 'RDP', 'RUP']
		feed_types = feed.keys()

		# Constraints: minimum nutrition requirements for cows
		# values here are coefficients (on the LHS of the eq)
		constraints = ration.calculate_constraints(feed, nutrients_list)
		# Objective: minimize total cost of all feeds
		objective = {feed_type: feed[feed_type]['price'] for feed_type in feed_types}
		# Maximum allowed use for each feed type
		limits = {feed_type: feed[feed_type]['limit'] for feed_type in feed_types}

		# Loop variables
		infeasible = True
		# scaling factor for base_MY (milk production figure)
		milk_production_power = 0
		milk_production_multiplier = 1.0

		#
		# Loop until ration formulated is feasible
		# If not feasible, scale down milk production figure (base_MY)
		# and try again
		# base_MY is scaled down by 5% for every iteration
		#
		while infeasible:
			# Constraints: minimum nutrition requirements for cows
			# values here are requiremtnts (on the RHS of constraint eq)
			# milk_production_multiplier is passed as scaling factor
			rqmts = ration.calculate_rqmts(self.parity, self.WIM, self.AMF,
										   self.BWR, self.base_NED, self.housing,
										   nutrients_list, milk_production_multiplier)
			formulated_ration = ration.optimize(constraints, rqmts, objective,
												limits, nutrients_list, feed_types)
			infeasible = (formulated_ration['status'] == 'Infeasible')

			milk_production_power += 1
			milk_production_multiplier = pow(0.95, milk_production_power)

		self.ration = formulated_ration

	def annual_reset(self):
		pass
