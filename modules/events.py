import json
import zmq
import traceback
from hon.packets import ID, sc_structs
import hon.packets
import threading

bot = None
sock = None
commandSock = None

def commandThread():
    while True:
        message = json.loads(commandSock.recv())
        if message[0] == 'chat':
            msg = '<%s> %s' % (message[2], message[3])
            print message
            bot.write_packet(hon.packets.ID.HON_CS_CHANNEL_MSG, msg, message[1])
        elif message[0] == 'privmsg':
            bot.write_packet(hon.packets.ID.HON_CS_WHISPER, message[1], message[2])
        else:
            print message

def setup(b):
    global bot, sock, commandSock
    bot = b

    try:
        context = zmq.Context()
        sock = context.socket(zmq.PUB)
        sock.bind('tcp://127.0.0.1:25892')

        commandSock = context.socket(zmq.SUB)
        commandSock.setsockopt(zmq.SUBSCRIBE, '')
        commandSock.connect('tcp://127.0.0.1:25893')

        thr = threading.Thread(None, commandThread)
        thr.daemon = True
        thr.start()
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
events.thread = False

eventStrings = {}
for k in dir(ID):
    eventStrings[getattr(ID, k)] = k

def monitor(bot, input):
    parts = input.split()
    print "Sending monitor request: %s" % (parts[1],)
    bot.write_packet(hon.packets.ID.HON_CS_MONITOR, parts[1])
monitor.commands = ['monitor']

def friend(bot, input):
    parts = input.split()
    print "Sending friend request: %s" % (parts[1],)
    bot.write_packet(hon.packets.ID.HON_CS_BUDDY_ADD_NOTIFY, parts[1])
friend.commands = ['friend']
