#!/usr/bin/env python
"""
"""

from hon.packets import ID
import re
from time import time

check_time = {}

def __cooldown(accountid):
	if accountid in check_time:
		if (check_time[accountid] + 60) > time():
			return False
		else:
			check_time[accountid] = time()
			return True
	else:
		check_time[accountid] = time()
		return True

def apply(bot, input):
	"""Check if you application has been successful, Once every minute"""
	try:
		if not bot.vb.Login(bot.config.forumuser,bot.config.forumpassword):
			bot.reply('Unable to check application at this time')
			print("Forum credentials are invaid")
			return
		toFind = r'username\?: (\w+)'
		if input.admin and input.group(2):
			nick = input.group(2).lower()
			aid = bot.nick2id[nick]
		else:
			nick = input.nick
			aid = input.account_id
		if not input.admin and not __cooldown(aid):
			return
		traineeApps = bot.vb.GetThreads(34, 30)
		for threadinfo in traineeApps:
			thread = threadinfo['thread']
			match = re.search(toFind, thread['preview'].lower())
			if match is not None and match.group(1) == nick:
				if thread['prefix_rich'].find("APPROVED") > 0:
					bot.reply("Welcome to Project Epoch, %s! Inviting now." % nick)
					if not aid in bot.clan_roster:
						bot.write_packet(ID.HON_CS_CLAN_ADD_MEMBER, nick)
						bot.reply("Invited!")
						bot.vb.NewPost( thread['threadid'], "Invited", "Player has been invited to the clan.")
					else:
						bot.reply("You're already in the clan?!")
						bot.vb.NewPost( thread['threadid'], "Invited", "Player has been invited to the clan. (By someone else)")
					bot.vb.MoveThread( thread['threadid'], 36 )
				elif thread['prefix_rich'].find("DENIED") > 0:
					bot.reply("Your application was denied.")
				else:
					bot.reply("Your application is still pending.")
				return
		mentorApps = bot.vb.GetThreads(35, 30)
		for threadinfo in mentorApps:
			thread = threadinfo['thread']
			match = re.search(toFind, thread['preview'].lower())
			if match is not None and match.group(1) == nick:
				if thread['prefix_rich'].find("APPROVED") > 0:
					bot.reply("Welcome to Project Epoch, %s!" % nick)
					if not aid in bot.clan_roster:
						bot.write_packet(ID.HON_CS_CLAN_ADD_MEMBER, nick)
						bot.reply("Invited!")
						bot.vb.NewPost( thread['threadid'], "Invited", "Player has been invited to the clan.")
					else:
						bot.reply("You're already in the clan?!")
						bot.vb.NewPost( thread['threadid'], "Invited", "Player has been invited to the clan. (By someone else)")
					bot.vb.MoveThread( thread['threadid'], 38 )
				elif thread['prefix_rich'].find("DENIED") > 0:
					bot.reply("Your application was denied.")
				else:
					bot.reply("Your application is still pending.")
				return
		bot.reply("No application found for your username.")
	except Exception as inst:
		print(inst)
		bot.reply('Unable to check application at this time')
apply.commands = ['apply']

if __name__ == '__main__': 
    print __doc__.strip()