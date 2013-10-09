import sys
import zmq
import json

context = zmq.Context()
sock = context.socket(zmq.SUB)
sock.setsockopt(zmq.SUBSCRIBE, '')
sock.connect('tcp://127.0.0.1:25892')

UNINTERESTING = 'HON_SC_PING HON_SC_TOTAL_ONLINE HON_SC_UPDATE_STATUS HON_SC_INITIAL_STATUS'.split()
CHANNEL = 'tkt'

users = {}
inMatch = {}
channelId = None

def recalculate():
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

while True:
    sender, message = json.loads(sock.recv())
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

        print "Chat message from %s: %s" % (users.get(uid, '???'), message[1])
    elif message[0] == "HON_SC_UPDATE_STATUS":
        # u'HON_SC_UPDATE_STATUS', 7719439, 5, 128, 0, u'', u'', u'white', u'Default Icon', u'5.153.24.250:11245', u'TMM Match #122447668', 122447668
        if message[1] not in users:
            continue
        username = users[message[1]]

        if len(message) >= 11:
            print "Player %s entered game #%s" % (username, message[11])
            inMatch[username] = message[11]
            recalculate()
        elif len(message) >= 10:
            print "Player %s entering server %s" % (username, message[9])
        else:
            if username in inMatch:
                print "Player %s not in game" % (username,)
                del inMatch[username]
                recalculate()
    elif message[0] in UNINTERESTING:
        pass
    else:
        print message
