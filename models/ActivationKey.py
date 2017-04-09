from datetime import datetime					# ActivationKey
import random									# ActivationKey
import string									# ActivationKey

from __main__ import db							# All models

class ActivationKey(db.Model):
	__tablename__ = 'activation_keys'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	user = db.relationship('User', backref=db.backref('activation_users', lazy='dynamic'))
	key = db.Column(db.String(16), unique=True)
	creation_date = db.Column(db.DateTime)

	@classmethod
	def generate(cls, length=8):
		key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))
		# Make sure the key is unique
		while ActivationKey.query.filter_by(key=key).one_or_none() is not None:
			key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))
		return key

	def __init__(self, user, key=None, creation_date=None):
		self.user = user
		if key is None:
			key = ActivationKey.generate()
		self.key = key
		if creation_date is None:
			creation_date = datetime.utcnow()
		self.creation_date = creation_date

	def __repr__(self):
		return "<ActivationKey(user='%s', key='%s', creation_date='%s')>" % (
			self.user.real_name, self.key, self.creation_date)
