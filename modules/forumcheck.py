#!/usr/bin/env python
"""
"""

from hon.packets import ID
import re
from time import time
from utils.forum import VB
import sys
import traceback

def setup(bot):
	bot.config.module_config('apply', [1, 'Enable application checking'])
	bot.config.module_config('apply_invite', [0, 'Enable automated inviting'])

check_time = {}
appForums = {
	34: "C",
	35: "C",
	# 36: "A", # What if they got kicked out? They could use this to get back in. So accepted subforum is ignored
	37: "D",
	# 38: "A", # What if they got kicked out? They could use this to get back in. So accepted subforum is ignored
	39: "D",
	50: "H",
	51: "M", # Morgue (Archive)
	52: "H",
	53: "M" # Morgue (Archive)
}

def __cooldown(accountid):
	if accountid in check_time:
		if (check_time[accountid] + 120) > time():
			return False
		else:
			check_time[accountid] = time()
			return True
	else:
		check_time[accountid] = time()
		return True

def cleanPreview(text):
	return text.replace("`", "").replace("_", "").lower()

def apply(bot, input):
	"""Check if you application has been successful, Once every minute"""
	try:
		if input.admin and input.group(2):
			nick = input.group(2).lower()
			if nick in bot.nick2id:
				aid = bot.nick2id[nick]
			else:
				aid = 0
		else:
			nick = input.nick
			aid = input.account_id
		if not input.admin and not __cooldown(aid):
			bot.reply("Please wait to use this command again")
			return
		if aid > 0 and aid in bot.clan_roster:
			bot.reply("You're already in {0}, silly.".format( bot.clan_info['name'] ))
			return
		if not input.admin and bot.config.apply == 0:
			bot.reply("In-Game application checking is disabled.")
			return
		bot.write_packet( ID.HON_SC_WHISPER, input.nick, "Fetching application status, please wait..." )
		bot.vb.Login(bot.config.forumuser, bot.config.forumpassword) # Session expiry check, this is instant if still under expiry time
		searchid = bot.vb.Search( 1, "in-game username?: {0}".format(nick) )
		if searchid:
			results = bot.vb.ProcessSearch(searchid)
			if len(results) == 0:
				bot.reply("No application found for your username.")
				return
			handled = False
			for result in results:
				thread = result['thread']
				appUsernameMatch = re.search(r'username\?: ([a-zA-Z0-9`_]+)', thread['preview'])
				appUsername = appUsernameMatch.group(1).lower()
				if int(thread['forumid']) in appForums and appUsername == nick:
					handled = True
					state = appForums[ int(thread['forumid']) ]
					if state == "C":
						if len(thread['prefix_rich']) > 0:
							if thread['prefix_rich'].find("APPROVED") > 0:
								state = "A"
							elif thread['prefix_rich'].find("DENIED") > 0:
								state = "D"
							elif thread['prefix_rich'].find("CHECK") > 0:
								state = "H"
						else:
							state = "H"
					if state == "A":
						if bot.config.apply_invite == 0:
							bot.reply("Your application was accepted. Please contact an officer to get invited.")
						else:
							bot.reply("Welcome to Project Epoch, %s!" % nick)
							bot.write_packet(ID.HON_CS_CLAN_ADD_MEMBER, nick)
							bot.reply("Invited!")
							if thread['forumid'] == 34:
								if bot.vb.NewPost( thread['threadid'], "Invited", "Player has been invited to the clan."):
									if bot.vb.MoveThread( thread['threadid'], 36 ):
										print("Success")
									else:
										print("Failed to move")
								else:
									print("Failed to post")
							elif thread['forumid'] == 35:
								bot.vb.NewPost( thread['threadid'], "Invited", "Player has been invited to the clan.")
								bot.vb.MoveThread( thread['threadid'], 38 )
					elif state == "D":
						bot.reply("Sorry, your application was denied. Ask an officer to find out why.")
					elif state == "H":
						bot.reply("Your application is pending.")
					elif state == "M":
						bot.reply("Your application was archived, result unknown. Contact an officer.")
					else:
						bot.reply("Unable to check application at this time")
					return
			if not handled:
				bot.reply("No application found for your username.")
		else:
			bot.reply('Unable to check application at this time')
			print("SearchID not returned")
	except Exception as inst:
		traceback.print_exc()
		bot.reply('Unable to check application at this time')
apply.commands = ['apply']
apply.thread = True

if __name__ == '__main__': 
    print __doc__.strip()