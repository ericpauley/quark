import redis
import threading
import json
from script_runner import *
r = redis.Redis()
ps = r.pubsub()

ps.subscribe("control")

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
finally:
    for k,v in scripts:
        v.stop()
