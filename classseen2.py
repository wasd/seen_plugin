#$ neutron_plugin 01
# --*-- encoding: utf-8 --*--

import re
from datetime import datetime
import pickle
import os
import threading

MSG_KEINE_FINDET = "Не видел никого."
MSG_ETWAS_FINDET = "Нашёл %d, вот они (отсортированные): "
MSG_MEHR_FINDET = "Нашёл %d, вот %d крайних (по алфавиту (или как-то ещё)): "
MSG_SAH_BEITRETEN = "%s зашёл %s."
MSG_SAH_FERLASSEN = "%s ушёл %s."
MSG_KEINE_WORT_GIBEN = "Вы ничего не докажете!"

maxfind = 5
SEEN_FILENAME = 'static/seen.txt'

seen_join='J'
seen_leave='L'

class LastSeen:
	def __init__ (self, filename):
		self._lock = threading.Lock()
		self.seen_dict = {}
		self.seen_list = []
		self.seen_filename = filename
		self._readfile()

	def add_join(self, groupchat, nick):
		self._add(nick, seen_join)

	def add_leave(self, groupchat, nick):
		self._add(nick, seen_leave)
	
	def _add(self, nick, flag):
		with self._lock:
			self.seen_dict[nick] = {'date': datetime.now(), 'flag': flag}
			while self.seen_list.count(nick):
				self.seen_list.remove(nick)
			self.seen_list.insert(0, nick)
			self._writefile()

	def _writefile(self):
		with open(self.seen_filename, 'wb') as fp:
			pickle.dump((self.seen_dict, self.seen_list), fp)

	def _readfile(self):
		try:
			with open(self.seen_filename, 'rb') as fp:
				try:
					(self.seen_dict, self.seen_list) = pickle.load(fp)
				except:
					self.seen_dict = {}
					self.seen_list = []
		except:
			pass

	def find(self, such, mode='wild'):
		findet = []
		if mode == 'wild':
			if such.endswith('*'):
				such = such[:-1]
				findet = [nick for nick in self.seen_list if nick.startswith(such)]
			elif self.seen_list.count(such):
				findet = [such]
		elif mode == 're':
			expr = re.compile(such, re.IGNORECASE|re.UNICODE)
			findet = [nick for nick in self.seen_list if expr.match(nick)]
		return findet

	def _get_flag(self, nick):
		return self.seen_dict[nick]['flag']

	def _get_date(self, nick):
		return self.seen_dict[nick]['date']

	def _get_seen(self, found, groupchat):
		result = ''
		count = len(found)
		if count == 0:
			return MSG_KEINE_FINDET
		nicks = ' '.join(found[0:maxfind])
		if count > maxfind:
			result += MSG_MEHR_FINDET % (count, maxfind) + nicks + '. '
		elif count > 1:
			result += MSG_ETWAS_FINDET % (count) + nicks + '. '
		latest = found[0]
		if self._get_flag(latest) == seen_join:
			result += MSG_SAH_BEITRETEN % (latest, self._get_date(latest).isoformat(' '))
		if self._get_flag(latest) == seen_leave:
			result += MSG_SAH_VERLASSEN % (latest, self._get_date(latest).isoformat(' '))
		# bug here
#		who = get_who(groupchat)
#		if who:
#			if who.has_key(latest):
#				result += ' %s ist noch hier' % latest
		# this is ugly hack proposed by bot code itself
		if GROUPCHATS[groupchat].has_key(latest):
			result += ' %s всё ещё здесь!' % latest
		return result

	def show(self, type, source, parameters):
		groupchat = get_groupchat(source)
		querast = source[2]
		if not groupchat:
			return
		if not parameters:
			msg(groupchat, MSG_KEINE_WORT_GIBEN)
			return
		suche = (parameters.split())[0].strip()
		antwort = querast+': '+self._get_seen(self.find(suche), groupchat)
		msg(groupchat, antwort)

	def show_re(self, type, source, parameters):
		groupchat = get_groupchat(source)
		querast = source[2]
		if not groupchat:
			return
		if not parameters:
			msg(groupchat, MSG_KEINE_WORT_GIBEN)
			return
		suche = (parameters.split())[0].strip()
		antwort = querast+': '+self._get_seen(self.find(suche, 're'), groupchat)
		msg(groupchat, antwort)

seen = LastSeen(SEEN_FILENAME)

register_command_handler(seen.show,u'!seen',0,u'seen',u'!seen',[u'!seen'])
register_command_handler(seen.show,u'!где',0,u'где',u'!где',[u'!где'])
register_command_handler(seen.show_re,u'!seenr',0,u'seenr',u'!seenr',[u'!seenr'])
register_leave_handler(seen.add_leave)
register_join_handler(seen.add_join)

#mynick = get_nick(groupchat)

