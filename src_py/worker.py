import redis
import threading
import json
from script_runner import *
import socket
import threading
import SocketServer
r = redis.Redis()
ps = r.pubsub()

ps.subscribe("control")

class MyTCPHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.id = self.rfile.readline().strip()
        r.hsetnx("associations", self.id, "")

        while True:
            device = r.hget("associations", self.id)
            data = self.rfile.readline().strip()
            self.wfile.write("ACK\n\r")
            print data

    def get_real_id():
        sketch,name = r.hget("associations",self.id).split(" ")



class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

HOST, PORT = "0.0.0.0", 1337

server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
ip, port = server.server_address

# Start a thread with the server -- that thread will then start one
# more thread for each request
server_thread = threading.Thread(target=server.serve_forever)
# Exit the server thread when the main thread terminates
server_thread.daemon = True
server_thread.start()

class ThreadedUDPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        cur_thread = threading.current_thread()
        print data

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

HOST, PORT = "0.0.0.0", 1337
server = SocketServer.ThreadedUDPServer((HOST, PORT), ThreadedUDPRequesthandler)

server_thread = threading.Thread(target=server.serve_forever)
# Exit the server thread when the main thread terminates
server_thread.daemon = True
server_thread.start()

scripts = {}
try:
    for message in ps.listen():
        if 'message' not in message['type']:
            continue
        print message['data']
        cmd = json.loads(message['data'])
        name = cmd['name']
        if cmd['cmd'] == "start":
            code = r.get(name+".code")
            if name in scripts:
                scripts[name].stop()
            scripts[name] = DataScript(name, code)
            print "Starting script!!!"
            scripts[name].start()
        if cmd['cmd'] == "stop":
            if name in scripts:
                scripts[name].stop()
finally:
    for k,v in scripts:
        v.stop()
