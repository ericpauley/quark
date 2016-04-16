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

    def start(self):
        threading.Thread(target=self.run).start()

    def stop(self):
        self.pubsub.reset()

    def run(self):
        self.running = True
        exec(self.script, self, self)
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
        self.running = False

    def stream(self, schan):
        try:
            schan = schan.chan # If the channel is not a string try to stringify it
        except:
            pass
        def decorator(func):
            chan = "%s.%s"%(self.name,schan)
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
        self.r.publish("%s.%s"%(self.name, chan),data)

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
