from datetime import datetime
from slugify import slugify
from flask import url_for

from __main__ import db, html_cleaner
from utils import html_image_extractor

association_table = db.Table('association_news_item_external_link',
	db.Column('news_item_id', db.Integer, db.ForeignKey('news_items.id'), nullable=False),
	db.Column('external_link_id', db.Integer, db.ForeignKey('external_links.id'), nullable=False),
	db.PrimaryKeyConstraint('news_item_id', 'external_link_id')
)

class NewsItem(db.Model):
	__tablename__ = 'news_items'

	id = db.Column(db.Integer, primary_key=True)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	author = db.relationship("User", backref="news_items")
	category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
	category = db.relationship("Category", backref="news_items")
	links = db.relationship("ExternalLink", secondary=association_table)
	headline_en = db.Column(db.String())
	headline_ja = db.Column(db.String())
	headline_nl = db.Column(db.String())
	headline_es = db.Column(db.String())
	headline_pt = db.Column(db.String())
	headline_kr = db.Column(db.String())
	summary_en = db.Column(db.String())
	summary_ja = db.Column(db.String())
	summary_nl = db.Column(db.String())
	summary_es = db.Column(db.String())
	summary_pt = db.Column(db.String())
	summary_kr = db.Column(db.String())
	subhead_en = db.Column(db.String())
	subhead_ja = db.Column(db.String())
	subhead_nl = db.Column(db.String())
	subhead_es = db.Column(db.String())
	subhead_pt = db.Column(db.String())
	subhead_kr = db.Column(db.String())
	body_en = db.Column(db.String())
	body_ja = db.Column(db.String())
	body_nl = db.Column(db.String())
	body_es = db.Column(db.String())
	body_pt = db.Column(db.String())
	body_kr = db.Column(db.String())
	is_draft_en = db.Column(db.Boolean)
	is_draft_ja = db.Column(db.Boolean)
	is_draft_nl = db.Column(db.Boolean)
	is_draft_es = db.Column(db.Boolean)
	is_draft_pt = db.Column(db.Boolean)
	is_draft_kr = db.Column(db.Boolean)
	date_created = db.Column(db.DateTime)
	carousel_image_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'), nullable=True)
	feature_image_full_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'), nullable=True)
	feature_image_small_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'), nullable=True)
	date_published = db.Column(db.DateTime)
	is_published = db.Column(db.Boolean)
	is_hidden = db.Column(db.Boolean)
	is_feature = db.Column(db.Boolean)	# Feature items are eligible to appear in the front page
	is_archived = db.Column(db.Boolean)	# Archived items do not accept new comments
	allows_comments = db.Column(db.Boolean)
	url = db.Column(db.String())
	comments = db.relationship("Comment", backref="news_item", order_by="Comment.date_posted")
	num_comments = db.Column(db.Integer)
	score = db.Column(db.Integer)
	slug = db.Column(db.String())
	
	def __init__(self, author_id, headline_en=None, headline_ja=None, headline_nl=None, headline_es=None, headline_pt=None, headline_kr=None, subhead_en=None, subhead_ja=None, subhead_nl=None, subhead_es=None, subhead_pt=None, subhead_kr=None, body_en=None, body_ja=None, body_nl=None, body_es=None, body_pt=None, body_kr=None, is_draft_en=True, is_draft_ja=True, is_draft_nl=True, is_draft_es=True, is_draft_pt=True, is_draft_kr=True, header_image_id=None, date_published=None, is_published=False, is_hidden=False, is_feature=False, is_archived=False, allows_comments=True, url=None, category_id=0, summary_en=None, summary_ja=None, summary_nl=None, summary_es=None, summary_pt=None, summary_kr=None, slug=None):
		self.author_id = author_id
		self.category_id = category_id
		self.headline_en = headline_en
		self.headline_ja = headline_ja
		self.headline_nl = headline_nl
		self.headline_es = headline_es
		self.headline_pt = headline_pt
		self.headline_kr = headline_kr
		self.subhead_en = subhead_en
		self.subhead_ja = subhead_ja
		self.subhead_nl = subhead_nl
		self.subhead_es = subhead_es
		self.subhead_pt = subhead_pt
		self.subhead_kr = subhead_kr
		self.summary_en = summary_en
		self.summary_ja = summary_ja
		self.summary_nl = summary_nl
		self.summary_es = summary_es
		self.summary_pt = summary_pt
		self.summary_kr = summary_kr
		self.body_en = html_cleaner.clean_html(body_en) if body_en else None
		self.body_ja = html_cleaner.clean_html(body_ja) if body_ja else None
		self.body_nl = html_cleaner.clean_html(body_nl) if body_nl else None
		self.body_es = html_cleaner.clean_html(body_es) if body_es else None
		self.body_pt = html_cleaner.clean_html(body_pt) if body_pt else None
		self.body_kr = html_cleaner.clean_html(body_kr) if body_kr else None
		self.is_draft_en = is_draft_en
		self.is_draft_ja = is_draft_ja
		self.is_draft_nl = is_draft_nl
		self.is_draft_es = is_draft_es
		self.is_draft_pt = is_draft_pt
		self.is_draft_kr = is_draft_kr
		self.date_created = datetime.utcnow()
		self.date_published = date_published or self.date_created
		self.is_published = is_published
		self.is_hidden = is_hidden
		self.is_feature = is_feature
		self.is_archived = is_archived
		self.allows_comments = allows_comments
		self.url = url
		self.num_comments = 0
		self.score = 0
		self.slug = slug

		self.html_extract_images()

	def html_extract_images(self):
		# Extract images embedded in the HTML
		params = {
			'add_classes': ['img-responsive'],
			'image_max_dimension': 1200,
			'lightbox_format_string': 'Images for news item %s'
		}
		self.body_en = html_image_extractor(self.body_en, **params)
		self.body_ja = html_image_extractor(self.body_ja, **params)
		self.body_nl = html_image_extractor(self.body_nl, **params)
		self.body_es = html_image_extractor(self.body_es, **params)
		self.body_pt = html_image_extractor(self.body_pt, **params)
		self.body_kr = html_image_extractor(self.body_kr, **params)

	def add_link(self, link):
		db.session.add(self)
		self.links.append(link)
		db.session.commit()
		
	def remove_link(self, link):
		db.session.add(self)
		self.links.remove(link)
		db.session.commit()

	def add_comment(self, comment):
		if comment is not None:
			db.session.add(self)
			self.comments.append(comment)
			self.num_comments = len(self.comments)
			db.session.commit()

	def add_feature_image(self, original_image):

		from . import StoredImage

		# Make a carousel image, exactly 1400x600
		carousel_image = StoredImage.from_original(original_image)
		carousel_image.fit_within(width=1400, height=1400)
		mid_height = carousel_image.height/2
		carousel_image.crop(0, mid_height-300, 1400, mid_height+300)

		# Make a feature image, exactly 1200x675
		feature_image_full = StoredImage.from_original(original_image)
		feature_image_full.fit_within(width=1200, height=1200)
		mid_height = feature_image_full.height/2
		feature_image_full.crop(0, mid_height-337, 1200, mid_height+338)

		# Make a small feature image, exactly 450x253
		feature_image_small = StoredImage.from_original(original_image)
		feature_image_small.fit_within(width=450, height=450)
		mid_height = feature_image_small.height/2
		feature_image_small.crop(0, mid_height-126, 450, mid_height+127)

		# Save the new images to the database   
		db.session.add(self)
		self.carousel_image_id = carousel_image.save_to_db()
		self.feature_image_full_id = feature_image_full.save_to_db()
		self.feature_image_small_id = feature_image_small.save_to_db()
		db.session.commit()	
