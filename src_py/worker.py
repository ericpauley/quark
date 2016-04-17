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

class Eater(threading.Thread):

    def __init__(self, caller):
        super(Eater,self).__init__()
        self.caller = caller

    def run(self):
        for i in self.caller():
            pass

class MyTCPHandler(SocketServer.StreamRequestHandler):

    def display(self, message):
        print "Displaying"
        self.wfile.write("S|%s\r"%message['data'])

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.id = self.rfile.readline().strip()
        print "id",self.id
        r.hsetnx("associations", self.id, "")
        self.wfile.write("S|CHOUCHIEEEEEEE\r")
        ps = r.pubsub()
        try:
            ps.subscribe(**{"device."+self.id+".display":self.display})
            Eater(ps.listen).start()
            while True:
                sketch,device = self.get_real_id()
                data = self.rfile.readline().strip()
                self.wfile.write("ACK\r")
                print data
        finally:
            ps.close()

    def get_real_id(self):
        return r.hget("associations",self.id).split(".")

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
        data = self.request[0].strip()
        #print data

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

HOST, PORT = "0.0.0.0", 1337
server = ThreadedUDPServer((HOST, PORT), ThreadedUDPRequestHandler)

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
            print "stop"
            if name in scripts:
                scripts[name].stop()
finally:
    for k,v in scripts:
        v.stop()
input()
