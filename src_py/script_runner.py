import redis
import time
import json

class DataScript(object):

    def __init__(self, id, script):
        self.id = id
        self.script = script
        self.r = redis.Redis()
        self.pubsub = self.r.pubsub()
        self.listeners = {}

    def run(self):
        exec(self.script, locals={}, globals=self.__dict__)
        for message in self.pubsub.listen():
            data = json.loads(message['data'])
            t = data['t']
            val = data['val']
            for listener in self.listeners.get(message['pattern']):
                listener(t, val)

    def stream(self, chan):
        def decorator(func):
            self.listeners[chan] = self.listeners.get(chan,())+(func,)
            self.pubsub.psubscribe(self.id+chan)
            return func

    def push(self, chan, val, t=None):
        if t is None:
            t = time.time()
        self.r.publish(dict(t=t,val=val))
