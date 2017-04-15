from __main__ import db							# All models

class ExternalLink(db.Model):
	__tablename__ = 'external_links'

	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String())
	title = db.Column(db.String())
	desc_en = db.Column(db.String())
	desc_ja = db.Column(db.String())
	desc_nl = db.Column(db.String())
	desc_es = db.Column(db.String())
	desc_pt = db.Column(db.String())
	desc_kr = db.Column(db.String())
	num_visits = db.Column(db.Integer)
	
	def __init__(self, url=None, title=None, desc_en=None, desc_ja=None, desc_nl=None, desc_es=None, desc_pt=None, desc_kr=None, ):
		self.url = url
		self.title = title
		self.desc_en = desc_en
		self.desc_ja = desc_ja
		self.desc_nl = desc_nl
		self.desc_es = desc_es
		self.desc_pt = desc_pt
		self.desc_kr = desc_kr
		self.num_visits = 0
