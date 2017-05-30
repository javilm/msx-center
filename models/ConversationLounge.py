from datetime import datetime
from sqlalchemy import desc
import lxml.html as LH

from __main__ import app, db

try:
	from models.ConversationThread import ConversationThread
except ImportError:
	import sys
	ConversationThread = sys.modules[__package__ + '.ConversationThread']
	app.logger.info("XXX thread = %s" % ConversationThread)
	

class ConversationLounge(db.Model):
	__tablename__ = 'lounges'

	id = db.Column(db.Integer, primary_key=True)
	name_en = db.Column(db.String())
	name_ja = db.Column(db.String())
	name_es = db.Column(db.String())
	name_nl = db.Column(db.String())
	name_pt = db.Column(db.String())
	name_kr = db.Column(db.String())
	desc_en = db.Column(db.String())
	desc_ja = db.Column(db.String())
	desc_es = db.Column(db.String())
	desc_nl = db.Column(db.String())
	desc_pt = db.Column(db.String())
	desc_kr = db.Column(db.String())
	allows_anonymous = db.Column(db.Boolean)
	allows_nicknames = db.Column(db.Boolean)
	allows_unverified = db.Column(db.Boolean)
	allows_new = db.Column(db.Boolean)
	allows_bad_reputation = db.Column(db.Boolean)
	staff_only = db.Column(db.Boolean)
	is_visible = db.Column(db.Boolean)
	is_readonly = db.Column(db.Boolean)
	num_threads = db.Column(db.Integer)
	priority = db.Column(db.Integer)
	color_class = db.Column(db.String())
	slug = db.Column(db.String())
	threads = db.relationship("ConversationThread", backref="lounge", order_by=desc("threads_first_post_date"))

	@classmethod
	def	get_permission_errors(cls, user, lounge):
		# Check the user's permission to post in the lounge
		user_errors = {}
		if user is None:
			if not lounge.allows_anonymous:
				user_errors['anonymous'] = True
		elif user.is_blocked:
			user_errors['blocked'] = True
		elif user.is_new and not lounge.allows_new:
			user_errors['new'] = True
		elif not user.is_verified and not lounge.allows_unverified:
			user_errors['unverified'] = True
		elif not user.is_staff and lounge.staff_only:
			user_errors['not_staff'] = True
		elif user.reputation < 0 and not lounge.allows_bad_reputation:
			user_errors['bad_reputation'] = True
		return user_errors

	def __init__(self, name_en, desc_en, name_ja=None, name_es=None, name_nl=None, name_pt=None, name_kr=None, desc_ja=None, desc_es=None, desc_nl=None, desc_pt=None, desc_kr=None, allows_anonymous=False, allows_nicknames=False, allows_unverified=False, allows_new=False, allows_bad_reputation=False, staff_only=True, is_visible=True, is_readonly=False, priority=10, color_class='success', slug=None):

		# Lounge name in several languages
		self.name_en = LH.document_fromstring(name_en).text_content() if name_en else ''
		self.name_ja = LH.document_fromstring(name_ja).text_content() if name_ja else ''
		self.name_nl = LH.document_fromstring(name_nl).text_content() if name_nl else ''
		self.name_es = LH.document_fromstring(name_es).text_content() if name_es else ''
		self.name_pt = LH.document_fromstring(name_pt).text_content() if name_pt else ''
		self.name_kr = LH.document_fromstring(name_kr).text_content() if name_kr else ''

		# Lounge description in several languages
		self.desc_en = LH.document_fromstring(desc_en).text_content() if desc_en else ''
		self.desc_ja = LH.document_fromstring(desc_ja).text_content() if desc_ja else ''
		self.desc_nl = LH.document_fromstring(desc_nl).text_content() if desc_nl else ''
		self.desc_es = LH.document_fromstring(desc_es).text_content() if desc_es else ''
		self.desc_pt = LH.document_fromstring(desc_pt).text_content() if desc_pt else ''
		self.desc_kr = LH.document_fromstring(desc_kr).text_content() if desc_kr else ''

		# Flags and metadata
		self.allows_anonymous = allows_anonymous
		self.allows_nicknames = allows_nicknames
		self.allows_unverified = allows_unverified
		self.allows_new = allows_new
		self.allows_bad_reputation = allows_bad_reputation
		self.staff_only = staff_only
		self.is_visible = is_visible
		self.is_readonly = is_readonly
		self.num_threads = 0
		self.priority = priority
		self.color_class = color_class
		self.slug = name_en

	def add_thread(self, thread):
		thread.lounge_id = self.id
		db.session.add(self)
		db.session.add(thread)
		self.num_threads = ConversationThread.query.filter_by(lounge_id=self.id).count()	# Recount to make it accurate
		db.session.commit()
