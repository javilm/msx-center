import copy, enum
from datetime import datetime
from lxml import etree
import lxml.html as LH
from flask import request, url_for
from __main__ import db
from __main__ import html_cleaner
from utils import get_host_by_ip 
from . import StoredImage

class ConversationMessage(db.Model):
	__tablename__ = 'messages'

	class PostAsType(enum.Enum):
		ANON = 'Anonymous'
		REALNAME = 'Real name'
		NICKNAME = 'Nickname'

	id = db.Column(db.Integer, primary_key=True)
	thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	body_en = db.Column(db.String())
	body_ja = db.Column(db.String())
	body_nl = db.Column(db.String())
	body_es = db.Column(db.String())
	body_pt = db.Column(db.String())
	body_kr = db.Column(db.String())
	score = db.Column(db.Integer)				# Message score. Calculated from the likes and dislikes
	post_as = db.Column(db.Enum(PostAsType))
	date_posted = db.Column(db.DateTime)
	is_reported = db.Column(db.Boolean)			# Reported for moderation
	is_hidden = db.Column(db.Boolean)			# Hidden by administration for any motive
	is_moderated = db.Column(db.Boolean)		# Hidden because it was moderated
	is_deleted = db.Column(db.Boolean)			# Deleted by the user (data remains in the database)
	is_staff_favorite = db.Column(db.Boolean)	# Favorited by the staff. Highlighted.
	remote_ip = db.Column(db.String())
	remote_host = db.Column(db.String())

	def __init__(self, user, post_as, body_en, body_ja=None, body_nl=None, body_es=None, body_pt=None, body_kr=None, remote_ip=None):
		if user is None:
			self.user_id = None
		else:
			self.user_id = user.id
		self.thread_id = None
		self.body_en = html_cleaner.clean_html(body_en) if body_en else None
		self.body_ja = html_cleaner.clean_html(body_ja) if body_ja else None
		self.body_nl = html_cleaner.clean_html(body_nl) if body_nl else None
		self.body_es = html_cleaner.clean_html(body_es) if body_es else None
		self.body_pt = html_cleaner.clean_html(body_pt) if body_pt else None
		self.body_kr = html_cleaner.clean_html(body_kr) if body_kr else None
		self.score = 0
		self.post_as = post_as	# ANON, REALNAME or NICKNAME
		self.date_posted = datetime.utcnow()
		self.is_reported = False
		self.is_hidden = False
		self.is_moderated = False
		self.is_deleted = False
		self.is_staff_favorite = False
		self.remote_ip = remote_ip or request.headers['X-Real-Ip']
		self.remote_host = get_host_by_ip(self.remote_ip)

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
			new.attrib['data-lightbox'] = 'Images for message %s' % self.id
			# Add the <img> tag inside the new <a> element
			new.append(tmp_element)

			# Replace the <img ...> tag in the HTML code with the new <a ...><img ...></a>
			element.getparent().replace(element, new)

			del img, tmp_img

		self.body_en = LH.tostring(root)


