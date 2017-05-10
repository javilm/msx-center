from datetime import datetime
from flask import request
from __main__ import app, db
from utils import format_datetime, get_host_by_ip

class Vote(db.Model):
	__tablename__ = 'votes'

	id = db.Column(db.Integer, primary_key=True)
	comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
	message_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
	member_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	score = db.Column(db.Integer)
	date_posted = db.Column(db.DateTime)
	remote_ip = db.Column(db.String())
	remote_host = db.Column(db.String())

	@classmethod
	def upvote_comment(cls, member=None, comment=None):

		# Check whether we can actually return a valid vote:
		if member is None or comment is None:
			return None

		# Checks whether there's already a vote on this comment from this member. If there is, do nothing. Otherwise, add the new vote.
		vote = Vote.query.filter_by(member_id=member.id, comment_id=comment.id).first()
		if vote is not None:
			return None
		else:
			return Vote(member=member, comment=comment, score=2)

	@classmethod
	def downvote_comment(cls, member=None, comment=None):

		# Check whether we can actually return a valid vote:
		if member is None or comment is None:
			return None

		# Checks whether there's already a vote on this comment from this member. If there is, do nothing. Otherwise, add the new vote.
		vote = Vote.query.filter_by(member_id=member.id, comment_id=comment.id).first()
		if vote is not None:
			return None
		else:
			return Vote(member=member, comment=comment, score=1)

	@classmethod
	def upvote_message(cls, member=None, message=None):

		# Check whether we can actually return a valid vote:
		if member is None or message is None:
			return None

		# Checks whether there's already a vote on this comment from this member. If there is, do nothing. Otherwise, add the new vote.
		vote = Vote.query.filter_by(member_id=member.id, message_id=message.id).first()
		if vote is not None:
			return None
		else:
			return Vote(member=member, message=message, score=2)

	@classmethod
	def downvote_message(cls, member=None, message=None):

		# Check whether we can actually return a valid vote:
		if member is None or message is None:
			return None

		# Checks whether there's already a vote on this comment from this member. If there is, do nothing. Otherwise, add the new vote.
		vote = Vote.query.filter_by(member_id=member.id, message_id=message.id).first()
		if vote is not None:
			return None
		else:
			return Vote(member=member, message=message, score=1)

	# Score:
	#	1: Downvote
	#	2: Upvote
	def __init__(self, member=None, comment=None, message=None, remote_ip=None, score=2):
		if member:
			self.member_id = member.id
			self.member = member
		if comment:
			self.comment_id = comment.id
			self.comment = comment
		elif message:
			self.message_id = message.id
			self.message = message

		self.score = score
		self.date_posted = datetime.utcnow()
		self.remote_ip = remote_ip or request.headers['X-Real-Ip']
		self.remote_host = get_host_by_ip(self.remote_ip)

	def formatted_datetime(self):
		return format_datetime(self.date_posted)
