#!/usr/bin/env python3
import sys, json, threading, time, socket


DEFAULT_HOST = '127.0.0.1'  # constant host since all routers are on the same machine
ROUTE_UPDATE_INTERVAL = 30
UPDATE_INTERVAL = 1


class State:
	def __init__(self):
		self.id = None					# current node id
		self.network = dict()   # adj list graph of network
		self.info = dict()      # details of all nodes ()

	def set_link(self, src_id, dest_id, weight):
		if src_id not in self.network:
			self.network[src_id] = {}
		if dest_id not in self.network:
			self.network[dest_id] = {}
		self.network[src_id][dest_id] = float(weight)
		self.network[dest_id][src_id] = float(weight)
	
	def set_info(self, id, host, port):
			self.info[id] = (host, int(port))

	def get_info(self, id):
		return self.info[id]

	def get_my_info(self):
		return self.get_info(self.id)

	def get_neighbours_info(self):
		info = self.info.copy()
		del info[self.id]
		return list(tuple(t) for t in info.values())

	def serialize(self):
		return json.dumps({ 'network': self.network , 'info': self.info })

	def deserialize(self, serialized):
		return json.loads(serialized)

	def update_state(self, serialized_state):
		updated = self.deserialize(serialized_state)
		new_ids = set(updated['info'].keys()).difference(set(self.info.keys()))
		# update info table
		self.info = { **self.info, **updated['info'] }
		# update existing ids in network
		for k in self.network.keys():
			if k in updated['network']:
				self.network[k] = { **self.network[k], **updated['network'][k] }
		# add new hosts to network
		for id in new_ids:
			self.network[id] = updated['network'][id]

	def __repr__(self):
		return	'{\n' \
						f'\tnetwork: {json.dumps(self.network, sort_keys=True)},\n' \
						f'\tinfo: {json.dumps(self.info, sort_keys=True)},\n' \
						'\n}'


class Router:
	def __init__(self):
		self.state = State()		# route state instance
		self.broadcasts = set() # cache containing sent broadcasts

	def setup(self, config_path):
		try:
			with open(config_path, 'r') as file:
				self.state.id, port = file.readline().split()
				self.state.set_info(self.state.id, DEFAULT_HOST, port)
				n = int(file.readline())
				for i in range(n):
					id, weight, port = file.readline().split()
					self.state.set_info(id, DEFAULT_HOST, port)
					self.state.set_link(self.state.id, id, weight)
			file.close()
		except Exception as e:
			print(f'Error loading {config_path}')
			print(e)

	def __broadcaster(self):
		while True:
			time.sleep(UPDATE_INTERVAL)
			client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			client_socket.settimeout(1.0)
			message = self.state.serialize()
			if message not in self.broadcasts:
				for host_info in self.state.get_neighbours_info():
					client_socket.sendto(message.encode(), host_info)
					try:
						response, server = client_socket.recvfrom(1024)
					except socket.timeout:
						# print('Broadcast Error: ', host_info)
						pass
				self.broadcasts.add(message)

	def __listener(self):
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		server_socket.bind(self.state.get_my_info())
		while True:
			response, address = server_socket.recvfrom(1024)
			self.state.update_state(response.decode())
			server_socket.sendto(response, address)

	def __processor(self):
		while True:
			time.sleep(ROUTE_UPDATE_INTERVAL)
			print(self.state)
			self.__processor()

	def run(self):
		services = [self.__broadcaster, self.__listener, self.__processor]
		for service in services:
			thread = threading.Thread(target=service, daemon=True)
			thread.start()
		while True: time.sleep(UPDATE_INTERVAL)		# keep main thread alive


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage: ./Lsr.py <config_file>')
		exit(1)
	router = Router()
	router.setup(sys.argv[1]) # load config
	router.run()
	