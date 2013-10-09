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

q = queue.Queue()
class HonIrcBot(irc.client.SimpleIRCClient):
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
ircBot.connect('irc.cc.tut.fi', 6667, 'NavettaBot-')
ircConn = ircBot.connection

def ircMsg(conn, msg):
    try:
        conn.privmsg(IRC_CHAN, msg[0:100])
    except irc.client.MessageTooLong:
        conn.privmsg(IRC_CHAN, "Message too long.")

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

UNINTERESTING = 'HON_SC_PING HON_SC_TOTAL_ONLINE HON_SC_UPDATE_STATUS HON_SC_INITIAL_STATUS'.split()
CHANNEL = 'tkt'

users = {}
inMatch = {}
channelId = None

def recalculate(conn):
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
    print (msg, users, inMatch)
    conn.notice(IRC_CHAN, msg)

while True:
    sender, message = json.loads(sock.recv())
    # ircMsg(ircConn, json.dumps(message))
    if message[0] == "HON_STATUS_INLOBBY":
        if message[1] != CHANNEL:
            continue

        users = {}
        channelId = message[2]
        print "Channel %s has id %s" % (CHANNEL, channelId)

        for tup in message[8]:
            if tup[2] == 5:
                # print 'Login: Player %s is in-game' % (tup[0],)
                inMatch[tup[0]] = -1
            users[tup[1]] = tup[0]

        recalculate(ircConn)
    elif message[0] == "HON_SC_LEFT_CHANNEL":
        if message[2] != channelId:
            continue

        if message[1] in users:
            del users[message[1]]
        recalculate(ircConn)
    elif message[0] == "HON_STATUS_INGAME":
        if message[1] != channelId:
            continue

        users[message[3]] = message[2]
        recalculate(ircConn)
    elif message[0] == "HON_STATUS_ONLINE":
        uid = sender[1]
        chid = sender[2]
        if chid != channelId:
            continue

        ircMsg(ircConn, "<%s> %s" % (users.get(uid, '???'), message[1]))
        print "<%s> %s" % (users.get(uid, '???'), message[1])
    elif message[0] == "HON_SC_UPDATE_STATUS":
        # u'HON_SC_UPDATE_STATUS', 7719439, 5, 128, 0, u'', u'', u'white', u'Default Icon', u'5.153.24.250:11245', u'TMM Match #122447668', 122447668
        if message[1] not in users:
            continue
        username = users[message[1]]

        if len(message) >= 11:
            print "Player %s entered game #%s" % (username, message[11])
            inMatch[username] = message[11]
            recalculate(ircConn)
        elif len(message) >= 10:
            print "Player %s entering server %s" % (username, message[9])
        else:
            if username in inMatch:
                print "Player %s not in game" % (username,)
                del inMatch[username]
                recalculate(ircConn)
    elif message[0] in UNINTERESTING:
        pass
    else:
        print message
