from __main__ import db							# All models

class ArticleSeries(db.Model):
	__tablename__ = 'article_series'

	id = db.Column(db.Integer, primary_key=True)
	title_en = db.Column(db.String)
	title_ja = db.Column(db.String)
	title_nl = db.Column(db.String)
	title_es = db.Column(db.String)
	title_pt = db.Column(db.String)
	title_kr = db.Column(db.String)
	desc_en = db.Column(db.String)
	desc_ja = db.Column(db.String)
	desc_nl = db.Column(db.String)
	desc_es = db.Column(db.String)
	desc_pt = db.Column(db.String)
	desc_kr = db.Column(db.String)
	is_numbered = db.Column(db.Boolean)
