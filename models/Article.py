import copy
from datetime import datetime
from lxml import etree
import lxml.html as LH
from slugify import slugify
from flask import url_for
from __main__ import html_cleaner, db
from . import StoredImage

association_table = db.Table('association_article_external_link',
	db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), nullable=False),
	db.Column('external_link_id', db.Integer, db.ForeignKey('external_links.id'), nullable=False),
	db.PrimaryKeyConstraint('article_id', 'external_link_id')
)

class Article(db.Model):
	__tablename__ = 'articles'

	id = db.Column(db.Integer, primary_key=True)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	author = db.relationship('User', backref='articles')
	category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
	category = db.relationship('Category', backref='articles')
	series_id = db.Column(db.Integer, db.ForeignKey('article_series.id'))
	series = db.relationship('ArticleSeries', backref='articles')
	chapter = db.Column(db.Integer)
	header_image_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'), nullable=True)
	links = db.relationship('ExternalLink', secondary=association_table)
	title_en = db.Column(db.String())
	title_ja = db.Column(db.String())
	title_nl = db.Column(db.String())
	title_es = db.Column(db.String())
	title_pt = db.Column(db.String())
	title_kr = db.Column(db.String())
	summary_en = db.Column(db.String())
	summary_ja = db.Column(db.String())
	summary_nl = db.Column(db.String())
	summary_es = db.Column(db.String())
	summary_pt = db.Column(db.String())
	summary_kr = db.Column(db.String())
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
	date_published = db.Column(db.DateTime)
	is_published = db.Column(db.Boolean)
	is_hidden = db.Column(db.Boolean)
	is_archived = db.Column(db.Boolean)	# Archived items do not accept new comments
	allows_comments = db.Column(db.Boolean)
	num_comments = db.Column(db.Integer)
	score = db.Column(db.Integer)
	slug = db.Column(db.String())
	
	def __init__(self, chapter=0, header_image_id=None, title_en=None, title_ja=None, title_nl=None, title_es=None, title_pt=None, title_kr=None, summary_en=None, summary_ja=None, summary_nl=None, summary_es=None, summary_pt=None, summary_kr=None, body_en=None, body_ja=None, body_nl=None, body_es=None, body_pt=None, body_kr=None, is_draft_en=True, is_draft_ja=True, is_draft_nl=True, is_draft_es=True, is_draft_pt=True, is_draft_kr=True, date_published=None, is_published=False, is_hidden=False, is_archived=False, allows_comments=True, slug=None):
		self.chapter = chapter
		self.header_image_id = header_image_id
		self.title_en = title_en
		self.title_ja = title_ja
		self.title_nl = title_nl
		self.title_es = title_es
		self.title_pt = title_pt
		self.title_kr = title_kr
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
		self.is_archived = is_archived
		self.allows_comments = allows_comments
		self.num_comments = 0
		self.score = 0
		self.slug = slug

		self.extract_images()

	def extract_images(self):
		root = LH.fromstring(self.body_en)

		for element in root.iter('img'):
			# Make a copy of the original HTML element
			tmp_element = copy.copy(element)

			# Generate an image by decoding the Base64 content of the src attribute
			img = StoredImage.from_datauri(element.attrib['src'])

			# Check based on the MD5 hash whether the image was already in the database, save it if it wasn't
			tmp_img = StoredImage.query.filter_by(md5_hash=img.md5_hash).first()
			if tmp_img is None:
				db.session.add(img)
				db.session.commit()
			else:
				img = tmp_img

			# Modify the attributes in the copy of the <img...> tag
			tmp_element.attrib['src'] = url_for('send_image', image_id=img.id, dummy_filename='msx-center_image_%s.%s' % (img.id, img._ext()))
			tmp_element.attrib['class'] = 'img-responsive'

			# Create a new <A ...> element that will contain the modified <IMG ...> tag
			new = etree.Element("a", href=tmp_element.attrib['src'])
			new.attrib['data-lightbox'] = 'Images for comment %s' % self.id
			# Add the <img> tag inside the new <a> element
			new.append(tmp_element)

			# Replace the <img ...> tag in the HTML code with the new <a ...><img ...></a>
			element.getparent().replace(element, new)

			del img, tmp_img

		self.body_en = LH.tostring(root)
