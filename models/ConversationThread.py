from datetime import datetime
from slugify import slugify

from __main__ import db
from __main__ import app

try:
	from . import ConversationLounge
except ImportError:
	import sys
	ConversationLounge = sys.modules[__package__ + '.ConversationLounge']
	app.logger.info("XXX lounge = %s" % ConversationLounge)

from . import ConversationMessage

class ConversationThread(db.Model):
	__tablename__ = 'threads'

	id = db.Column(db.Integer, primary_key=True)
	lounge_id = db.Column(db.Integer, db.ForeignKey('lounges.id'))
	title_en = db.Column(db.String())
	title_ja = db.Column(db.String())
	title_nl = db.Column(db.String())
	title_es = db.Column(db.String())
	title_pt = db.Column(db.String())
	title_kr = db.Column(db.String())
	is_popular = db.Column(db.Boolean)
	is_trending = db.Column(db.Boolean)
	is_sticky = db.Column(db.Boolean)
	num_views = db.Column(db.Integer)
	num_messages = db.Column(db.Integer)
	first_post_date = db.Column(db.DateTime)
	last_post_date = db.Column(db.DateTime)
	slug = db.Column(db.String())
	messages = db.relationship("ConversationMessage", backref="thread")

	@classmethod
	def	get_permission_errors(cls, user, thread):
		# Threads inherit the posting permissions from the lounge they're in. Get the lounge object and call the class method.
		return ConversationLounge.get_permission_errors(user, thread.lounge)

	def __init__(self, title_en=None, title_ja=None, title_nl=None, title_es=None, title_pt=None, title_kr=None):
		self.lounge_id = None
		self.title_en = title_en
		self.title_ja = title_ja
		self.title_nl = title_nl
		self.title_es = title_es
		self.title_pt = title_pt
		self.title_kr = title_kr
		self.is_popular = False
		self.is_trending = False
		self.is_sticky = False
		self.num_views = 0
		self.num_messages = 0
		self.first_post_date = datetime.utcnow()
		self.last_post_date = self.first_post_date
		self.slug = slugify(unicode(title_en))

	def add_message(self, message):
		message.thread_id = self.id
		db.session.add(self)
		db.session.add(message)
		self.num_messages = ConversationMessage.query.filter_by(thread_id=self.id).count()	# Recount to make it accurate instead of just num_messages += 1
		self.last_post_date = datetime.utcnow()
		db.session.commit()
