from datetime import datetime
from flask import request, url_for
from __main__ import db, html_cleaner
from utils import get_host_by_ip, html_image_extractor, format_datetime

class Comment(db.Model):
	__tablename__ = 'comments'

	id = db.Column(db.Integer, primary_key=True)
	article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
	news_item_id = db.Column(db.Integer, db.ForeignKey('news_items.id'))
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	author = db.relationship('User', backref='comments')
	votes = db.relationship('Vote', backref='comment')
	body_en = db.Column(db.String())
	body_ja = db.Column(db.String())
	body_nl = db.Column(db.String())
	body_es = db.Column(db.String())
	body_pt = db.Column(db.String())
	body_kr = db.Column(db.String())
	score = db.Column(db.Integer)				# Message score. Calculated from the upvotes and downvotes
	num_upvotes = db.Column(db.Integer)			# Total upvotes 
	num_downvotes = db.Column(db.Integer)		# Total downvotes
	date_posted = db.Column(db.DateTime)
	is_reported = db.Column(db.Boolean)			# Reported for moderation
	is_hidden = db.Column(db.Boolean)			# Hidden by administration for any motive
	is_moderated = db.Column(db.Boolean)		# Hidden because it was moderated
	is_deleted = db.Column(db.Boolean)			# Deleted by the user (data remains in the database)
	is_staff_favorite = db.Column(db.Boolean)	# Favorited by the staff. Highlighted.
	remote_ip = db.Column(db.String())
	remote_host = db.Column(db.String())

	def __init__(self, author=None, body_en=None, body_ja=None, body_nl=None, body_es=None, body_pt=None, body_kr=None, remote_ip=None):
		if author is None:
			self.author_id = None
		else:
			self.author_id = author.id
		self.author = author
		self.article_id = None
		self.news_item_id = None
		self.body_en = html_cleaner.clean_html(body_en) if body_en else None
		self.body_ja = html_cleaner.clean_html(body_ja) if body_ja else None
		self.body_nl = html_cleaner.clean_html(body_nl) if body_nl else None
		self.body_es = html_cleaner.clean_html(body_es) if body_es else None
		self.body_pt = html_cleaner.clean_html(body_pt) if body_pt else None
		self.body_kr = html_cleaner.clean_html(body_kr) if body_kr else None
		self.score = 0
		self.num_upvotes = 0
		self.num_downvotes = 0
		self.date_posted = datetime.utcnow()
		self.is_reported = False
		self.is_hidden = False
		self.is_moderated = False
		self.is_deleted = False
		self.is_staff_favorite = False
		self.remote_ip = remote_ip or request.headers['X-Real-Ip']
		self.remote_host = get_host_by_ip(self.remote_ip)

		self.html_extract_images()

	def html_extract_images(self):

		# Extract images embedded in the HTML
		params = {
			'add_classes': ['img-responsive'],
			'image_max_dimension': 1200,
			'lightbox_format_string': 'Images for comment'
		}
		self.body_en = html_image_extractor(self.body_en, **params)
		self.body_ja = html_image_extractor(self.body_ja, **params)
		self.body_nl = html_image_extractor(self.body_nl, **params)
		self.body_es = html_image_extractor(self.body_es, **params)
		self.body_pt = html_image_extractor(self.body_pt, **params)
		self.body_kr = html_image_extractor(self.body_kr, **params)

	def formatted_datetime(self):
		return format_datetime(self.date_posted)

	def add_vote(self, vote):

		from . import Vote

		if vote:
			self.votes.append(vote)
			db.session.add(vote)
			self.update_score()

	def update_score(self):

		from . import Vote

		self.num_upvotes = Vote.query.filter_by(comment_id=self.id, score=2).count()
		self.num_downvotes = Vote.query.filter_by(comment_id=self.id, score=1).count()
		self.score = self.num_upvotes - self.num_downvotes
		db.session.add(self)
		db.session.commit()
