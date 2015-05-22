#!/usr/bin/python

class Song(object):

	def __init__(self, lyrics):
		self.lyrics = lyrics

	def sing_me_a_song(self):
		for line in self.lyrics:
			print line

happy_bday = Song(["Happy birthday to you",
					"I don't want to get sued",
					"So I'll stop right there"])

bulls_on_parade = Song(["They rally around the family",
						"With pockets full of shells"])

three_oclock_rock = Song(["We're going to rock this town",
					  "Rock it inside out"])

new_suede_shoes = Song(["You can do antyhing that you want to do",
					"But, don't you step on my blue suede shoes"])

happy_bday.sing_me_a_song()

bulls_on_parade.sing_me_a_song()

three_oclock_rock.sing_me_a_song()

new_suede_shoes.sing_me_a_song()