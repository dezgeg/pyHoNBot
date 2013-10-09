import json
import zmq
import traceback
from hon.packets import ID, sc_structs

try:
    context = zmq.Context()
    sock = context.socket(zmq.PUB)
    sock.bind('tcp://127.0.0.1:25892')
except Exception as e:
    traceback.print_exc()
    raise

def events(bot,*args): 
    arg1, arg2 = args

    if isinstance(arg2, str) or isinstance(arg2, unicode):
        arg2 = [arg2]
    # print (eventStrings.get(arg1[0], '?'), arg1, arg2)
    o = [arg1, [eventStrings.get(arg1[0], arg1[0])] + arg2]
    js = json.dumps(o)
    print js
    sock.send(js)

events.event = sc_structs.keys()
events.priority = 'low'

eventStrings = {}
for k in dir(ID):
    eventStrings[getattr(ID, k)] = k
