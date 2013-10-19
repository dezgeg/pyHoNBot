import os
import sys
import zmq
import json
import time
import threading
import Queue as queue
import irc
import irc.client
IRC_CHAN = '#tkt-hon'

channelId = None
honSock = None

q = queue.Queue()
class HonIrcBot(irc.client.SimpleIRCClient):
    def on_pubmsg(self, connection, event):
        global channelId
        if not channelId:
            print "EVERYTHING IS BROKEN, RESTART"
        else:
            sender = event.source.split('!')[0]
            honSock.send(json.dumps(['chat', channelId, sender, event.arguments[0]]))

    def on_join(self, connection, event):
        q.put('connected')

    def on_welcome(self, connection, event):
        print "Registered."
        connection.join(IRC_CHAN)

    def on_disconnect(self, connection, event):
        print "Disconnected."
        q.put('failed')

def handler(connection, event):
    print (event.type, event.source, event.target, event.arguments)

ircBot = HonIrcBot()
ircBot.ircobj.add_global_handler('all_raw_messages', handler, 0)
print "Connecting..."
ircBot.connect('irc.cs.hut.fi', 6667, 'NavettaBot')
ircConn = ircBot.connection

def ircMsg(msg):
    try:
        ircConn.privmsg(IRC_CHAN, msg[0:200])
    except irc.client.MessageTooLong:
        print ("********** Message too long", len(msg), msg)

def threadFunc():
    print "IRC thread starting"
    ircBot.start()

ircThread = threading.Thread(None, threadFunc)
ircThread.daemon = True
ircThread.start()

print "Waiting for registration..."
q.get()
print "Ready to accept HoN events."

context = zmq.Context()
sock = context.socket(zmq.SUB)
sock.setsockopt(zmq.SUBSCRIBE, '')
sock.connect('tcp://127.0.0.1:25892')

context = zmq.Context()
honSock = context.socket(zmq.PUB)
honSock.bind('tcp://127.0.0.1:25893')

CHANNEL = 'tkt'

users = {}
inMatch = {}

latestStatusMsg = None
def timerFunc():
    global latestStatusMsg
    print latestStatusMsg
    try:
        ircConn.notice(IRC_CHAN, latestStatusMsg[0:200])
    except irc.client.MessageTooLong:
        print ("********** Message too long", len(msg), msg)
noticeTimer = threading.Timer(2, timerFunc)

def recalculate():
    global latestStatusMsg, noticeTimer
    notInMatch = []
    matchDict = {}
    for id, username in users.iteritems():
        if username not in inMatch:
            notInMatch.append(username)
        else:
            matchId = inMatch[username]
            if not matchId in matchDict:
                matchDict[matchId] = []
            matchDict[matchId].append(username)

    matchStr = ' '.join([players[0] if len(players) == 1 else '(' + ' '.join(players) + ')' for id, players in matchDict.iteritems()])
    msg = 'Lobby: %s | In-game: %s' % (' '.join(notInMatch), matchStr)

    if msg != latestStatusMsg:
        print "Start timer"
        noticeTimer.cancel()
        noticeTimer = threading.Timer(2, timerFunc)
        latestStatusMsg = msg
        noticeTimer.start()

while True:
    sender, message = json.loads(sock.recv())
    # ircMsg(json.dumps(message))
    if message[0] == "HON_STATUS_INLOBBY":
        if message[1] != CHANNEL:
            continue

        users = {}
        inMatch = {}
        channelId = message[2]

        for tup in message[8]:
            if tup[2] == 5:
                inMatch[tup[0]] = -1
            users[tup[1]] = tup[0]

        recalculate()
    elif message[0] == "HON_SC_LEFT_CHANNEL":
        if message[2] != channelId:
            continue

        if message[1] in users:
            del users[message[1]]
        recalculate()
    elif message[0] == "HON_STATUS_INGAME":
        if message[1] != channelId:
            continue

        users[message[3]] = message[2]
        recalculate()
    elif message[0] == "HON_STATUS_ONLINE":
        uid = sender[1]
        chid = sender[2]
        if chid != channelId:
            continue

        ircMsg("<%s> %s" % (users.get(uid, '???'), message[1]))
    elif message[0] == "HON_SC_UPDATE_STATUS":
        if message[1] not in users:
            continue
        username = users[message[1]]

        if len(message) >= 11:
            print "Player %s entered game #%s" % (username, message[11])
            inMatch[username] = message[11]
            recalculate()
        else:
            if username in inMatch:
                print "Player %s not in game" % (username,)
                del inMatch[username]
                recalculate()
    else:
        print message
