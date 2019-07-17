#!/usr/bin/env python3
import sys, json

DEFAULT_HOST = '127.0.0.1'  # constant host since all routers are on the same machine
ROUTE_UPDATE_INTERVAL = 30

class State:
	def __init__(self):
		self.id = None					# current node id
		self.network = dict()   # adj list graph of network
		self.info = dict()      # details of all nodes ()
		self.broadcasts = set() # cache of already send broadcasts

	def add_link(self, src_id, dest_id, weight):
		if src_id not in self.network:
			self.network[src_id] = {}
		if dest_id not in self.network:
			self.network[dest_id] = {}
		self.network[src_id][dest_id] = float(weight)
		self.network[dest_id][src_id] = float(weight)
	
	def add_info(self, id, host, port):
			self.info[id] = (host, int(port))

	def load(self, config_path):
		with open(config_path, 'r') as file:
			self.id, port = file.readline().split()
			self.add_info(id=self.id, host=DEFAULT_HOST, port=port)
			n = int(file.readline())
			for i in range(n):
				id, weight, port = file.readline().split()
				self.add_info(id=id, host=DEFAULT_HOST, port=port)
				self.add_link(src_id=self.id, dest_id=id, weight=weight)
		file.close()

	def __repr__(self):
		return	'{\n' \
						f'\tnetwork: {self.network},\n' \
						f'\tinfo: {self.info},\n' \
						f'\tbroadcasts: {self.broadcasts}'\
						'\n}'

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage: ./Lsr.py <config_file>')
		exit(1)
	config_path = sys.argv[1]
	state = State()
	state.load(config_path)
	print(state)
