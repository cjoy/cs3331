#!/usr/bin/env python3 
from socket import *
import sys, os

def parse_request(request):
  components = request.decode().split(' ')
  request_type = components[0]
  request_file = components[1]
  return request_type, request_file

def is_image(request_file):
  ext = request_file.split('.')[-1]
  img_types = ['png', 'jpg', 'gif']
  return True if ext in img_types else False

def WebServer(host, port):
  print(f'WebServer serving on {host} on port {port}')
  with socket(AF_INET, SOCK_STREAM) as s:
    s.bind((host, port))
    s.listen(1)
    while True:
      conn, addr = s.accept()
      print(f'Request from {addr}')
      request = conn.recv(1024)
      request_type, request_file = parse_request(request)
      try:
        # ERROR if not GET request
        if request_type != 'GET':
          header = 'HTTP/1.0 500 Bad Request\n\n'.encode()
          conn.send(header)
          conn.close()
        # Handle image requests
        if is_image(request_file):
          with open(f'.{request_file}', 'rb') as file:
            if request_type == 'GET':
              header = 'HTTP/1.0 200 OK\nContent-Type: image/bmp\n\n'.encode()
              body = file.read()
              conn.send(header)
              conn.send(body)
              conn.close()
              print(f'Served {addr} with {request_file}')
            file.close()
        else:
          # Handle other requests (assuming html)
          with open(f'.{request_file}') as file:
            if request_type == 'GET':
              header = 'HTTP/1.0 200 OK\nContent-Type: text/html\n\n'.encode()
              body = file.read().encode()
              conn.send(header)
              conn.send(body)
              conn.close()
              print(f'Served {addr} with {request_file}')
            file.close()
      except IOError:
        header = 'HTTP/1.0 404 File Not Found\n\n'.encode()
        conn.send(header)
        conn.close()
        print(f'Unable to serve {addr} with {request_file}')



if __name__ == "__main__":
  host = '127.0.0.1'
  port = int(sys.argv[1])
  WebServer(host, port)

