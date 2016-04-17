import redis
import threading
import json
from script_runner import *
import socket
import threading
import SocketServer
import time
r = redis.Redis()
ps = r.pubsub()

ps.subscribe("control")

offsets = {}

class Eater(threading.Thread):

    def __init__(self, caller):
        super(Eater,self).__init__()
        self.caller = caller

    def run(self):
        for i in self.caller():
            pass

class MyTCPHandler(SocketServer.StreamRequestHandler):

    def display(self, message):
        self.wfile.write("S|%s\r"%message['data'])

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.id = self.rfile.readline().strip()
        del offsets[self.id]
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

def tint(i):
    try:
        return float(i)
    except:
        return i

class ThreadedUDPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip().split("|")
        id = data[0]
        millis = int(data[1])
        data = data[2:]
        data = {d.split(":")[0]:[float(i) for i in d.split(":")[1:]] for d in data}
        sketch, device = r.hget("associations",id).split(".")
        offset = time.time()-millis
        offsets[id] = offset
        prefix = "%s.chans.%s."%(sketch,device)
        if "Al" in data:
            r.publish(prefix+"accel.x", json.dumps(dict(t=millis+offset, val=data["Al"][0])))
            r.publish(prefix+"accel.y", json.dumps(dict(t=millis+offset, val=data["Al"][1])))
            r.publish(prefix+"accel.z", json.dumps(dict(t=millis+offset, val=data["Al"][2])))
        if "A0" in data:
            r.publish(prefix+"analog.0", json.dumps(dict(t=millis+offset, val=data["A0"][0])))
        if "A1" in data:
            r.publish(prefix+"analog.1", json.dumps(dict(t=millis+offset, val=data["A1"][0])))
        if "A2" in data:
            r.publish(prefix+"analog.2", json.dumps(dict(t=millis+offset, val=data["A2"][0])))
        if "Ml" in data:
            r.publish(prefix+"mag.x", json.dumps(dict(t=millis+offset, val=data["Ml"][0])))
            r.publish(prefix+"mag.y", json.dumps(dict(t=millis+offset, val=data["Ml"][1])))
            r.publish(prefix+"mag.z", json.dumps(dict(t=millis+offset, val=data["Ml"][2])))
        if "Bl" in data:
            r.publish(prefix+"pressure", json.dumps(dict(t=millis+offset, val=data["Bl"][0])))
            r.publish(prefix+"temp", json.dumps(dict(t=millis+offset, val=data["Bl"][1])))

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
