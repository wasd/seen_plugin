#$ neutron_plugin 01
# --*-- encoding: utf-8 --*--

import re
from datetime import datetime
import pickle
import os
import threading

MSG_KEINE_FINDET = "Ich habe niemanden gesehen."
MSG_ETWAS_FINDET = "Ich fand %d, hier sie (sortiert): "
MSG_MEHR_FINDET = "Ich fand %d, hier %d letzten (sortiert): "
MSG_SAH_BEITRETEN = "%s hat hereinkommt %s"
MSG_SAH_FERLASSEN = "%s hat verlasse uns %s"
MSG_KEINE_WORT_GIBEN = "Der kwaken der boloten der schloep der schloep der schloep."

maxfind = 5
SEEN_FILENAME = 'static/seen.txt'

seen_join='J'
seen_leave='L'

class LastSeen:
	__lock = threading.Lock()
	def __init__ (self, filename):
		self.seen_dict = {}
		self.seen_list = []
		self.seen_filename = filename
		self.__readfile()

	def add_join(self, groupchat, nick):
		self.__add(nick, seen_join)

	def add_leave(self, groupchat, nick):
		self.__add(nick, seen_leave)
	
	def __add(self, nick, flag):
		with self.__lock:
			self.seen_dict[nick] = {'date': datetime.now(), 'flag': flag}
			while self.seen_list.count(nick):
				self.seen_list.remove(nick)
			self.seen_list.insert(0, nick)
			self.__writefile()

	def __writefile(self):
		with open(self.seen_filename, 'wb') as fp:
			pickle.dump((self.seen_dict, self.seen_list), fp)

	def __readfile(self):
		try:
			with open(self.seen_filename, 'rb') as fp:
				try:
					(self.seen_dict, self.seen_list) = pickle.load(fp)
				except:
					self.seen_dict = {}
					self.seen_list = []
		except:
			pass

	def find(self, such):
		found = []
		if such.endswith('*'):
			such = such[:-1]
			found = [nick for nick in self.seen_list if nick.startswith(such)]
		elif self.seen_list.count(such):
			found = [such]
		return found

	def __get_flag(self, nick):
		return self.seen_dict[nick]['flag']

	def __get_date(self, nick):
		return self.seen_dict[nick]['date']

	def __get_seen(self, found):
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
		if self.__get_flag(latest) == seen_join:
			result += MSG_SAH_BEITRETEN % (latest, self.__get_date(latest).isoformat(' '))
		if self.__get_flag(latest) == seen_leave:
			result += MSG_SAH_VERLASSEN % (latest, self.__get_date(latest).isoformat(' '))
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
		antwort = self.__get_seen(self.find(suche))
		msg(groupchat, antwort)

seen = LastSeen(SEEN_FILENAME)

register_command_handler(seen.show,u'!sah',0,u'sah',u'!sah',[u'!sah'])
register_leave_handler(seen.add_leave)
register_join_handler(seen.add_join)
