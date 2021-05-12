import random as rand
import time
import math
import os
# my classes
import Node
import CoinStats as CS
import exchange as ex


class Bot():

	network_size = [4,5,3]
	path_to_configs = "../config_files/"
	path_to_histories = "../histories/"
	fees = .0052 # .005 = .5%

	def __init__(self, config_filename = None, parent = None, percent_d = None):
		self.network = []
		self.history = None
		for layer in self.network_size:
			new_layer = [None] * layer
			self.network.append(new_layer)
		if config_filename is not None:
			self.generate_from_config(config_filename)
		elif parent is not None:
			assert(percent_d is not None)
			self.generate_child(parent, percent_d)
		else:
			self.generate_random_net()

	def generate_random_net(self):
		empty_list = []
		for layer_index in range(len(self.network_size)):
			layer = self.network_size[layer_index]
			for node in range(layer):
				if layer_index == 0: # no need for weights
					self.network[0][node] = Node.Node(rand.random(),empty_list)
				else:
					weights = []
					for x in range(prev_layer): # generate random weights between 0 and 1
						weights.append(rand.random())
					self.network[layer_index][node] = Node.Node(rand.random(),weights)
			prev_layer = layer

	def generate_from_config(self, filename):
		print("GENERATING FROM CONFIGS: "+self.path_to_configs+filename)
		f = open(self.path_to_configs+filename)
		data = f.read()
		all_data = data.split("\n")
		node_index = 0
		for layer in self.network_size:
			for node in range(layer):
				node_data = all_data[node_index].split(",")
				layer_index = 0
				temp_node_index = node_index
				for layer_size in self.network_size:
					if temp_node_index >= layer_size:
						layer_index+=1
						temp_node_index-=layer_size
					else:
						break
				#print("Layer:",layer_index,"Index:",temp_node_index)
				if layer_index == 0:
					self.network[layer_index][temp_node_index] = Node.Node(node_data[0])
				else:
					self.network[layer_index][temp_node_index] = Node.Node(node_data[0], node_data[1:])
				node_index+=1
		f.close()

	def generate_child(self, parent_bot, percent_d):
		assert(self.network_size == parent_bot.network_size)
		empty_list = []
		for layer_index in range(len(self.network_size)):
			layer = self.network_size[layer_index]
			for node in range(layer):
				if layer_index == 0: # no need for weights
					delta = percent_d*rand.uniform(-1.0,1.0)
					bias = parent_bot.network[0][node].get_bias()
					bias = bias+delta
					self.network[0][node] = Node.Node(bias,empty_list)
				else:
					weights = parent_bot.network[layer_index][node].get_weights()
					bias = parent_bot.network[layer_index][node].get_bias()
					for x in range(prev_layer): # generate random weights between 0 and 1
						delta = percent_d*rand.uniform(-1.0,1.0)
						weights[x] = weights[x]+delta
					delta = percent_d*rand.uniform(-1.0,1.0)
					bias = bias+delta
					self.network[layer_index][node] = Node.Node(bias,weights)
			prev_layer = layer

	def write_config(self, filename):
		if os.path.exists(self.path_to_configs+filename):
			os.remove(self.path_to_configs+filename)
			time.sleep(.5)
		f = open(self.path_to_configs+filename, "w+")
		node_index = 0
		layer_index = 0
		net_size = len(self.network)-1
		while (layer_index!=net_size) or (node_index!=self.network_size[net_size]):
			if node_index == self.network_size[layer_index]: # go to next layer
				node_index = 0
				layer_index +=1
			#print("LAYER:",layer_index,"INDEX:",node_index)
			current_node = self.network[layer_index][node_index]
			f.write(str(current_node.get_bias()))
			if layer_index != 0: # dont index -1
				f.write(",")
				prev_layer_size = self.network_size[layer_index-1]
				for i in range(prev_layer_size-1):
					f.write(str(current_node.get_weight(i))+",")
				f.write(str(current_node.get_weight(prev_layer_size-1))+"\n")
			else:
				f.write("\n")
			node_index+=1 # progress onward ------->>
		f.close()

	def set_history(self, history_data):
		self.history = history_data

	def write_history(self, buy_file, sell_file):
		assert(self.history is not None)
		buys = self.history[0]
		sells = self.history[1]
		f = open(self.path_to_histories+buy_file, "w+")
		for x in range(len(buys)):
			f.write(str(buys[x][0])+","+str(buys[x][1])+"\n")
		f.close()
		f = open(self.path_to_histories+sell_file,"w+")
		for y in range(len(sells)):
			f.write(str(sells[y][0])+","+str(sells[y][1])+"\n")
		f.close()


	## HELPER FUNCTIONS FOR PROPAGATION
	def activate(self, layer, node): # Utilizes TanH Normalizer
		if layer != 0:
			new_value = self.network[layer][node].get_bias()
			this_node = self.network[layer][node]
			for x in range(self.network_size[layer-1]):
				prev_node = self.network[layer-1][x]
				new_value += prev_node.get_value()*this_node.get_weight(x)
			activated_value = math.tanh(new_value)
			#activated_value = new_value
			self.network[layer][node].set_value(activated_value)

	def propagate(self): # Runs network
		for layer_index in range(len(self.network_size)): 
			layer = self.network_size[layer_index]
			for node_index in range(layer):
				self.activate(layer_index, node_index)

	def determine_output(self): # Determine Output
		final_layer_index = len(self.network_size)-1
		assert(self.network_size[final_layer_index] == 3)
		node_0_val = self.network[final_layer_index][0].get_value()
		node_1_val = self.network[final_layer_index][1].get_value()
		node_2_val = self.network[final_layer_index][2].get_value()
		if (node_0_val >= node_1_val):
			if (node_0_val >= node_2_val):
				return 0
			else:
				return 2
		else:
			if (node_1_val >= node_2_val):
				return 1
			else:
				return 2

	def feed_data(self, input_data):
		assert(len(input_data) == self.network_size[0])
		for i in range(len(input_data)):
			self.network[0][i].set_value(input_data[i]+self.network[0][i].get_bias())


def train(data_csvs, num_instances, num_generations, config_file = None):
	path_to_prices = "../dogecoin_price_history/"
	all_data = []
	best_of_all_val = -100000.0
	best_of_all = None
	value = 0.0
	for data_csv in data_csvs:
		f = open(path_to_prices+data_csv)
		data = f.read()
		all_data.append(data)
	if config_file is not None:
		best_of_all_val, best_of_all = run_sim(all_data,config_file=config_file)
		print("Starting Value:",best_of_all_val)
	for i in range(num_generations):
		best_of_gen = None
		best_of_gen_val = -1000000.0
		for j in range(num_instances):
			if best_of_all is None:
				value, network = run_sim(all_data)
				print(str(j)+" : "+str(value))
			else:
				delta = math.pow(j/float(num_instances-1),2.0)
				value, network = run_sim(all_data,parent=best_of_all,percent_d=delta)
				print(str(delta)+" : "+str(value))
			if value > best_of_gen_val:
				best_of_gen_val = value
				best_of_gen = network
		print("BEST OF GENERATION: "+ str(best_of_gen_val))
		#value, test_bot = run_sim(all_data, parent=best_of_gen, percent_d=0)
		#print("CALCULATED BoG: "+ str(value))
		if best_of_gen_val > best_of_all_val:
			#print("BEST_OF_GEN_VAL: "+str(best_of_gen_val)+" BEST_OF_ALL_VAL: "+str(best_of_all_val))
			best_of_all_val = best_of_gen_val
			best_of_all = best_of_gen
		print("GEN "+str(i)+": "+str(best_of_gen_val))
	#best_of_all.write_config("boa.conf")
	return best_of_all_val, best_of_all


'''
def train_deprecated(data_csv, num_instances, num_generations, config_file = None):
	f = open(data_csv)
	data = f.read()
	if config_file is None:
		best_of_all = None
		best_of_all_val = -100000
	else:
		best_of_all_val, best_of_all = run_sim(data,config_file=config_file)
		print("Starting Value:",best_of_all_val)
	for i in range(num_generations):
		best_of_gen = None
		best_of_gen_val = -100000
		for j in range(num_instances):
			if best_of_all is None:
				value, network = run_sim(data)
			else:
				delta = math.pow(j/float(num_instances-1),2.0)
				#print(delta)
				value, network = run_sim(data,parent=best_of_all,percent_d=delta)
			if value > best_of_gen_val:
				best_of_gen_val = value
				best_of_gen = network
		if best_of_gen_val > best_of_all_val:
			best_of_all_val = best_of_gen_val
			best_of_all = best_of_gen
		print("GEN "+str(i)+": "+str(best_of_gen_val))
	return best_of_all_val, best_of_all
'''


def train_rewrite(data_csvs, num_instances, num_gens, config_file=None):
	# Function: Trains the neural net via test_data
	# Inputs:
	# 	data_csvs: array of filenames with training data
	# 	num_instances: number of nets to test per generation
	# 	num_gens: the number of generations to run the test for
	# 	config_file (OPTIONAL): configuration file to start the training with
	path_to_price_files = "../dogecoin_price_history/"
	all_data = []
	for data_csv in data_csvs:
		f = open(path_to_price_files+data_csv)
		data = f.read()
		f.close()
		all_data.append(data)
	all_net = Bot()
	all_val = -100000
	if config_file is not None:
		all_val, all_net = run_sim(all_data, config_file=config_file)
	print("STARTING UP: "+str(all_val))
	inst_val, inst_net = 0.0, Bot()
	for gen in range(num_gens):
		gen_net = Bot()
		gen_val = -10000000
		for instance in range(num_instances):
			if all_val < 0:
				inst_val, inst_net = run_sim(all_data)
				print("all_val < 0: " + str(inst_val) + " ")
			else:
				delta = math.pow(instance/float(num_instances-1),2.0)
				inst_val, inst_net = run_sim(all_data, parent=all_net, percent_d=delta)
			if inst_val > gen_val:
				gen_val = inst_val
				gen_net = inst_net
		print("BEST_OF_GEN_"+str(gen)+": "+str(gen_val))
		gen_net.write_config("gen_"+str(gen)+".csv")
		if gen_val >= all_val:
			#print("BEST_OF_GEN_VAL: "+str(gen_val)+" BEST_OF_ALL_VAL: "+str(all_val))
			all_val = gen_val
			all_net = gen_net
	print("BEST_OF_ALL: "+str(all_val))
	return all_val, all_net


def run_sim(data, config_file = None, parent = None, percent_d = None):
	buys = []
	sells = []
	doge_wallet = 0.0
	money = 100.00
	last_money = money
	last_interaction_price = 0.0
	if parent is not None:
		assert(percent_d is not None)
		net = Bot(parent=parent, percent_d=percent_d)
	elif config_file is not None:
		net = Bot(config_filename=config_file)
	else:
		net = Bot()
	data_entry = 0
	first = True
	for single_data in data:
		all_data = single_data.split("\n")
		times = []
		prices = []
		#have_doge = False
		#bought_price = 0.00
		for data_slice in all_data:
			if data_slice != "":
				slice_pieces = data_slice.split(",")
				time = float(slice_pieces[0])
				price = float(slice_pieces[1])
				if first:
					last_interaction_price = price
					first = False
				times[:0] = [time]
				prices[:0] = [price]
				times = times[:10]
				prices = prices[:10]
				if len(times) == 10:
					data = []
					'''
					if have_doge: # How much I'm up or down, 0
						data.append((prices[0]/bought_price)-1.0)
					else:
						data.append(0.00)
					'''
					#print(prices)
					#print(times)
					#data.append(calc_slope(times[:3],prices[:3])*10e4) # Slope, 0
					#data.append(calc_curl(times[:3],prices[:3])*10e5) # Curl, 1
					sum = 0.0
					for x in prices:
						sum += x
					average = sum/10.0
					data.append((prices[0] - average)/float(prices[0])) # Perc_from_Average, 2
					data.append((prices[0]-last_interaction_price)/float(last_interaction_price)) # Dist from last interact price, 2
					data.append(calc_slope(times,prices)*10e5) # Momentum, 3
					data.append(calc_curl(times,prices)*10e6) # Delta Momentum, 4
					#print(data)
					net.feed_data(data)
					net.propagate()
					output = net.determine_output()
					if output == 0:
						if (money > 50.00):
							last_interaction_price = prices[0]
							doge_delta = math.floor((money*.95)/prices[0])
							#doge_delta = (money*.95)/prices[0]
							doge_wallet += doge_delta
							last_money = money
							money -= calc_dues(float(doge_delta)*prices[0], net.fees, True)
							hit = [(86400.00*data_entry)+time,price]
							buys.append(hit)
					elif output == 2:
						if (doge_wallet > 50):
							last_interaction_price = prices[0]
							doge_delta = doge_wallet
							doge_wallet = 0
							hit = [(86400.00*data_entry)+time,price]
							money += calc_dues(float(doge_delta)*prices[0], net.fees, False)
							last_money = money
							sells.append(hit)
			
		data_entry += 1
	doge_delta = doge_wallet
	doge_wallet = 0
	money += (float(doge_delta)*prices[0])
	#print(money)
	decisions = [buys,sells]
	net.set_history(decisions)
	return last_money, net


def run_real(EXCHANGE, coin, coin_label, balance_file, minimum_crypto, config_file=None):
	buys = []
	sells = []
	times = []
	prices = []
	CS_OBJ = CS.CoinStats(coin)
	history_ext = "../histories"
	buy_file = "buy_"+str(CS_OBJ.day_no)+".csv"
	sell_file = "sell_"+str(CS_OBJ.day_no)+".csv"
	net = Bot(config_filename=config_file)
	last_interaction_price = 0.0
	first = True
	while True:
		if CS_OBJ.check_price():
			c_price = CS_OBJ.last_price
			c_time = CS_OBJ.last_time
			if first:
					last_interaction_price = c_price
					first = False
			prices[:0] = [c_price]
			times[:0] = [c_time]
			prices = prices[:10]
			times = times[:10]
			if len(times) == 10:
				data = []
				#print(prices)
				#print(times)
				#data.append(calc_slope(times[:3],prices[:3])*10e4) # Slope, 0
				#data.append(calc_curl(times[:3],prices[:3])*10e5) # Curl, 1
				sum = 0.0
				for x in prices:
					sum += x
				average = sum/10.0
				data.append((prices[0] - average)/float(prices[0])) # Perc_from_Average, 2
				data.append((prices[0]-last_interaction_price)/float(last_interaction_price)) # Dist from last interact price, 2
				data.append(calc_slope(times,prices)*10e5) # Momentum, 3
				data.append(calc_curl(times,prices)*10e6) # Delta Momentum, 4
				#print(data)
				net.feed_data(data)
				net.propagate()
				output = net.determine_output()
				if output == 0:
					money = EXCHANGE.default_balances["USD"]
					useable_funds = round((money*.99),2)
					if (useable_funds/float(prices[0]) > minimum_crypto):
						#hit = [time,price]
						#buys.append(hit)
						EXCHANGE.create_trade("USD",coin_label,useable_funds)
						wait_for_confirmation(EXCHANGE)
						EXCHANGE.save_balance(balance_file)
						print(EXCHANGE.default_balances)
						
				elif output == 2:
					crypto_wallet = EXCHANGE.default_balances[coin_label]
					useable_crypto = round(crypto_wallet*.99,4)
					if (useable_crypto > minimum_crypto):
						#hit = [time,price]
						#sells.append(hit)
						EXCHANGE.create_trade(coin_label,"USD",useable_crypto)
						wait_for_confirmation(EXCHANGE)
						EXCHANGE.save_balance(balance_file)
						print(EXCHANGE.default_balances)

		time.sleep(1)


# More Helper Functions
def wait_for_confirmation(EXCHANGE):
	while not EXCHANGE.check_trades():
		time.sleep(1)


def calc_slope(times, prices):
	sum = 0.0
	for i in range(len(times)-1):
		sum += (prices[i+1]-prices[i])*(times[i+1]-times[i])
	avg = sum/float(times[-1]-times[0])
	return avg


def calc_curl(times, prices):
	pre_curl = 0.0
	for i in range(len(times)-1):
		pre_curl += (prices[i+1]-prices[i])
	curl = pre_curl/float(times[-1]-times[0])
	return curl


def calc_dues(money, percentage, add):
	if add:
		post_fees = money + (money*percentage)
	else:
		post_fees = money - (money*percentage)
	return post_fees
