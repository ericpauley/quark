import redis
import time
import json
import re
from datetime import datetime
import stdlib
import threading

class DataScript(dict):

    def __init__(self, name, script):
        self.name = name
        self.script = script
        self.r = redis.Redis()
        self.pubsub = self.r.pubsub()
        self.listeners = {}
        self.nodes = {}
        self['d'] = self
        self.update(stdlib.__dict__)
        self.running = False
        self.graphs = []

    def start(self):
        threading.Thread(target=self.run).start()

    def graph(*args):
        graph = []
        for i in args:
            try:
                i = i.chan
            except:
                pass
            graph.append(i)
        graphs.append(graph)

    def stop(self):
        self.pubsub.reset()

    def run(self):
        try:
            print "Starting"
            self.running = True
            self.r.set("%s.running"%self.name,2)
            self.r.publish("%s.running"%self.name,2)
            exec(self.script, self, self)
            self.r.publish("%s.graphs"%self.name,json.dumps(self.graphs))
            self.r.set("%s.running"%self.name,1)
            self.r.publish("%s.running"%self.name,1)
            for message in self.pubsub.listen():
                if message['type'] != 'pmessage':
                    continue
                data = json.loads(message['data'])
                chan = message['channel']
                schan = ".".join(chan.split(".")[1:])
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
                                raise e
                        break
        finally:
            print "Ending"
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
        try:
            return super(DataSccript, self).__getitem__(name)
        except:
            return getattr(self, name)


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
