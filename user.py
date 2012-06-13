#!/usr/bin/python2.6

class User:
	
	# static member
	users = []

	@staticmethod
	def getCount():
		return len(User.users)

	def __init__(self, uid, name, sex, meeting_sex):
		self.uid = uid
		self.name = name
		self.sex = sex
		self.meeting_sex = meeting_sex
		self.musics = []
		self.movies = []
		self.score = 0

	# writer
	def set_movies(self, movies):
		self.movies = movies
	def set_musics(self, musics):
		self.musics = musics
	def increment_score(self):
		self.score += 1

	# reader
	def get_uid(self):
		return self.uid
	def get_name(self):
		return self.name
	def get_sex(self):
		return self.sex
	def get_meeting_sex(self):
		return self.meeting_sex
	def get_movies(self):
		return self.movies
	def get_musics(self):
		return self.musics
	def get_score(self):
		return self.score