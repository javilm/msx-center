import lxml.html as LH

from __main__ import db							# All models

class Category(db.Model):
	__tablename__ = 'categories'

	id = db.Column(db.Integer, primary_key=True)
	name_en = db.Column(db.String())
	name_ja = db.Column(db.String())
	name_nl = db.Column(db.String())
	name_es = db.Column(db.String())
	name_pt = db.Column(db.String())
	name_kr = db.Column(db.String())

	def __init__(self, name_en=None, name_ja=None, name_nl=None, name_es=None, name_pt=None, name_kr=None):
		self.name_en = LH.document_fromstring(name_en).text_content() if name_en else ''
		self.name_ja = LH.document_fromstring(name_ja).text_content() if name_ja else ''
		self.name_nl = LH.document_fromstring(name_nl).text_content() if name_nl else ''
		self.name_es = LH.document_fromstring(name_es).text_content() if name_es else ''
		self.name_pt = LH.document_fromstring(name_pt).text_content() if name_pt else ''
		self.name_kr = LH.document_fromstring(name_kr).text_content() if name_kr else ''
