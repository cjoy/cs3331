#!/usr/bin/env python3
import socket, sys, time, statistics


def ping_client(host, port):
  clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  clientSocket.settimeout(1)

  received = 0
  rtts = []
  for seq in range(10):
    message = f'PING {seq} {time.time()} \r\n'.encode()
    try:
      start = int(round(time.time() * 1000))
      clientSocket.sendto(message, (host, port))
      modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
      end = int(round(time.time() * 1000))
      rtt = end - start
      rtts.append(rtt)
      print(f'ping to {host}, seq = {seq}, rtt = {rtt} ms')
      received += 1
    except socket.timeout as e:
      print(f'ping to {host}, seq = {seq}, rtt = time out')
  
  # Statistics
  print(f'--- {host} ping statistics ---')
  print('10 packets transmitted, '
        f'{received} packets received, '
        f'{100 - ((received/10)*100)}% packet loss')
  print('round-trip min/avg/max/stddev = '
        f'{"%.3f" % min(rtts)}/'
        f'{"%.3f" % statistics.mean(rtts)}/'
        f'{"%.3f" % max(rtts)}/'
        f'{"%.3f" % statistics.stdev(rtts)} ms')
  clientSocket.close()



if __name__ == '__main__':
  if len(sys.argv) < 3:
    print('Usage: ./PingClient <host> <port>')
    exit(1)
  host = sys.argv[1]
  port = int(sys.argv[2])
  ping_client(host, port)
