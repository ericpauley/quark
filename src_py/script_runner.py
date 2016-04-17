import redis
import time
import json
import re
from datetime import datetime
import stdlib
import threading
import traceback
from time import time
from exceptions import Exception
import os
import sys

class DataScript(dict):

    def __init__(self, name, script):
        self.name = name
        self.script = script
        self.r = redis.Redis()
        self.pubsub = self.r.pubsub()
        self.listeners = {}
        self.nodes = {}
        self['d'] = self
        self.environ = {}
        self.environ.update(stdlib.__dict__)
        self.environ["log"] = self.log
        self.environ['d'] = self
        #self.update(__builtins__)
        self.running = False
        self.graphs = []
        self.updates = []
        self.lastrepeat = time()

    def start(self):
        threading.Thread(target=self.run).start()

    def log(self, data):
        self.r.publish("%s.logs"%self.name, json.dumps({"type":"primary","text":data.strip()}))
        self.r.rpush("%s.logs"%self.name, data.strip())

    def graph(self,*args, **kwargs):
        graph = []
        for i in args:
            try:
                i = i.chan
            except:
                pass
            i = "%s.%s.%s"%(self.name,"chans",i)
            graph.append(i)
        graph = {"channels":graph,"title":kwargs.get("title","Graph %s"%(len(self.graphs)+1))}
        self.graphs.append(graph)

    def stop(self):
        self.pubsub.reset()

    def device_listeners(self):
        @self.stream("*.display")
        def display(device,data):
            id = self.r.hget(self.name+".devices", device.chan)
            self.r.publish("device."+id+".display", data.val)
	@self.stream("*.digitalWrite")
        def digitalWrite(device,data):
            id = self.r.hget(self.name+".devices", device.chan)
            self.r.publish("device."+id+".digitalWrite", data.val)
        @self.stream("*.PWM")
        def PWM(device,data):
            id = self.r.hget(self.name+".devices", device.chan)
            self.r.publish("device."+id+".PWM", data.val)


    def run(self):
        try:
            self.r.publish("%s.logs"%self.name, json.dumps({"type":"info","text":"Program started..."}))
            print "Starting"
            self.running = True
            self.r.set("%s.running"%self.name,2)
            self.r.publish("%s.running"%self.name,2)
            self.device_listeners()
            exec(self.script, self.environ, self.environ)
            self.pubsub.subscribe("null")
            print "%s.graphs"%self.name
            self.r.publish("%s.graphs"%self.name,json.dumps(self.graphs))
            self.r.set("%s.running"%self.name,1)
            self.r.publish("%s.running"%self.name,1)
            while self.pubsub.subscribed:
                n = time()
                if n > self.lastrepeat + .1:
                    for method in self.updates:
                        method()
                    self.lastrepeat = n
                message = self.pubsub.get_message(ignore_subscribe_messages=True)
                if message is None:
                    continue
                data = json.loads(message['data'])
                chan = message['channel']
                schan = ".".join(chan.split(".")[2:])
                sensor = getattr(self, schan)
                device = sensor.device
                t = datetime.fromtimestamp(data['t'])
                val = data['val']
                dp = Datapoint(t=t,val=val)
                sensor.append(dp)
                if len(sensor) > 10:
                    sensor.pop(0)
                for listener in self.listeners.get(message['pattern'], ()):
                    kwargs = dict(chan=sensor,device=device,data=dp)
                    while True:
                        try:
                            listener(**kwargs)
                        except TypeError as e: # Remove offending kwargs until function is happy
                            m = re.match(r"\w+\(\) got an unexpected keyword argument '(\w+)'", e.message)
                            if m is not None:
                                del kwargs[m.group(1)]
                                continue
                            else:
                                traceback.print_exc()
                                self.r.publish("%s.logs"%self.name, json.dumps({"type":"danger","text":traceback.format_exc()}))
                                break
                        break
        except:
            self.r.publish("%s.logs"%self.name, json.dumps({"type":"danger","text":traceback.format_exc()}))
        finally:
            print "Ending"
            self.r.publish("%s.logs"%self.name, json.dumps({"type":"info","text":"Program ended..."}))
            self.running = False
            self.r.set("%s.running"%self.name,0)
            self.r.publish("%s.running"%self.name,0)

    def stream(self, schan):
        try:
            schan = schan.chan # If the channel is not a string try to stringify it
        except:
            pass
        def decorator(func):
            chan = "%s.%s.%s"%(self.name,"chans",schan)
            self.listeners[chan] = self.listeners.get(chan,())+(func,)
            self.pubsub.psubscribe(chan)
            print self.listeners
            return func
        return decorator

    def repeat(self, func):
        self.updates.append(func)
        return func

    def push(self, chan, val, t=None):
        try:
            chan = chan.chan # If the channel is not a string try to stringify it
        except:
            pass
        if isinstance(val, Datapoint):
            val,t = val.val,val.t
        if t is None:
            t = datetime.now()
        print t
        data = json.dumps(dict(t=(t - datetime(1970,1,1)).total_seconds(),val=val))
        self.r.publish("%s.%s.%s"%(self.name,"chans",chan),data)

    def __getattr__(self, attr):
        if attr not in self.nodes:
            self.nodes[attr] = Node(self, attr)
        return self.nodes[attr]

    def __getitem__(self, name):
        print self, name in self
        return super(DataScript, self).get(name, getattr(self, name))


class Node(list):

    def __init__(self,script,name):
        self.script = script
        self.name = name

    def push(self, val, t=None):
        self.script.push(self.chan,val,t)

    @property
    def chan(self):
        return self.name

    @property
    def device(self):
        return getattr(self.script, self.name.split(".")[0])

    def __getattr__(self,attr):
        return getattr(self.script, self.name+"."+attr)

class Datapoint(object):

    def __init__(self, t, val):
        self.t = t
        self.val = val

    def __add__(self, dp):
        return Datapoint(max(self.t,dp.t), self.val+dp.val)

    def __radd__(self, dp):
        if isinstance(dp, Datapoint):
            return Datapoint(max(self.t,dp.t), self.val+dp.val)
        return self

    def __div__(self, i):
        return Datapoint(self.t, self.val/i)

    def __str__(self):
        return "%s : %s"%(self.t,self.val)
