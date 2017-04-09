from __main__ import db							# All models

class ExternalLink(db.Model):
	__tablename__ = 'external_links'

	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String())
	num_visits = db.Column(db.Integer)
	
	def __init__(self, url=None):
		self.url = url
		self.num_visits = 0
