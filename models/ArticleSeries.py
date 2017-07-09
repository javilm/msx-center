from __main__ import db							# All models
from . import Article

class ArticleSeries(db.Model):
	__tablename__ = 'article_series'

	id = db.Column(db.Integer, primary_key=True)
	title_en = db.Column(db.String())
	title_ja = db.Column(db.String())
	title_nl = db.Column(db.String())
	title_es = db.Column(db.String())
	title_pt = db.Column(db.String())
	title_kr = db.Column(db.String())
	desc_en = db.Column(db.String())
	desc_ja = db.Column(db.String())
	desc_nl = db.Column(db.String())
	desc_es = db.Column(db.String())
	desc_pt = db.Column(db.String())
	desc_kr = db.Column(db.String())
	is_numbered = db.Column(db.Boolean)
	is_hidden = db.Column(db.Boolean)
	category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
	category = db.relationship('Category')
	slug = db.Column(db.String())
	priority = db.Column(db.Integer)
	num_articles = db.Column(db.Integer)
	date_newest_article = db.Column(db.DateTime)

	@classmethod
	def list_for_navbar(cls):
		return cls.query.filter(ArticleSeries.is_hidden=='f').order_by(ArticleSeries.priority).all()

	def add_article(self, article):
		self.articles.append(article)
		# Update the number of articles in this series
		self.num_articles = Article.query.filter(Article.is_published==True).filter(Article.is_draft_en==False).filter(Article.is_hidden==False).filter(Article.series_id == self.id).count()
		db.session.add(self)
		db.session.commit()
		
