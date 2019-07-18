#!/usr/bin/env python3
import sys, json, threading, time, socket
from enum import Enum, auto

ROUTE_UPDATE_INTERVAL = 30
UPDATE_INTERVAL = 1
DEFAULT_HOST = '127.0.0.1'

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

	def del_host(self, id):
		# remove adj list
		if id in self.network:
			del self.network[id]
		# remove host info
		if id in self.info:
			del self.info[id]
		# update other links
		for k in self.network:
			if id in self.network[k]:
				del self.network[k][id]

	def set_info(self, id, host, port):
			self.info[id] = [host, int(port)]

	def get_info(self, id):
		return self.info[id]

	def get_my_info(self):
		return self.get_info(self.id)

	def get_neighbours(self):
		info = self.info.copy()
		del info[self.id]
		return info.keys()

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
	MSG_STATE = 'STATE'
	MSG_DELIMITER = '|'
	MSG_HELLO = 'HELLO'
	HELLO_TTL = 3

	def __init__(self):
		self.state = State()	# route state instance
		self.broadcasts = {}	# cache containing sent broadcasts
		self.ttl = {}

	def __broadcaster(self):
		while True:
			time.sleep(UPDATE_INTERVAL)
			client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			client_socket.settimeout(1.0)
			state_message = self.__encode_msg(self.MSG_STATE, self.state.serialize())
			hello_message = self.__encode_msg(self.MSG_HELLO, self.state.id)
			for id in self.state.get_neighbours():
				host_info = self.state.get_info(id)
				if id not in self.broadcasts:
					self.broadcasts[id] = set()
				# send state message to neighbours
				if state_message not in self.broadcasts[id]:
					client_socket.sendto(state_message, tuple(host_info))
					self.broadcasts[id].add(state_message)
				# send state hello to neighbours (keep-alive)
				client_socket.sendto(hello_message, tuple(host_info))
			client_socket.close()

	def __listener(self):
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		server_socket.bind(tuple(self.state.get_my_info()))
		while True:
			response, address = server_socket.recvfrom(1024)
			msg_type, msg_data = self.__decode_msg(response)
			if msg_type == self.MSG_STATE:
				# update state if recieved state packet
				self.state.update_state(msg_data)
			elif msg_type == self.MSG_HELLO:
				# init host ttl as per hello protocol
				self.ttl[msg_data] = self.HELLO_TTL

	def __updater(self):
		while True:
			time.sleep(UPDATE_INTERVAL)
			# update trackers every second
			for id in list(self.ttl.keys()):
				if self.ttl[id] <= 0:
					# remove host broadcast cache if host's dead
					if id in self.broadcasts:
						del self.broadcasts[id]
					# remove from network
					self.state.del_host(id)
				else:
					# update ttl if still alive
					self.ttl[id] -= 1

	def __processor(self):
		while True:
			time.sleep(ROUTE_UPDATE_INTERVAL)
			print(self.state)

	def __encode_msg(self, msg_type, msg_data):
		return f'{msg_type}{self.MSG_DELIMITER}{msg_data}'.encode()

	def __decode_msg(self, encoded_msg):
		decoded_msg = encoded_msg.decode()
		msg_type, msg_data = decoded_msg.split(self.MSG_DELIMITER)
		return msg_type, msg_data

	def setup(self, config_path):
		with open(config_path, 'r') as file:
			self.state.id, port = file.readline().split()
			self.state.set_info(self.state.id, DEFAULT_HOST, port)
			n = int(file.readline())
			for i in range(n):
				id, weight, port = file.readline().split()
				self.state.set_info(id, DEFAULT_HOST, port)
				self.state.set_link(self.state.id, id, weight)
		file.close()

	def run(self):
		services = [self.__broadcaster, self.__listener, self.__updater, self.__processor]
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
	