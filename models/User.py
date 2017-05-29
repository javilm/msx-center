from datetime import datetime
import enum, hashlib, pycountry, random, re, string
from flask import render_template, url_for, session
from flask_mail import Message
from geoip import geolite2
from __main__ import db, mail, app

class User(db.Model):
	__tablename__ = 'users'

	class PreferredLanguageType(enum.Enum):
		EN = 'en'
		JA = 'ja'
		ES = 'es'
		PT = 'pt'
		NL = 'nl'
		KR = 'kr'

	id = db.Column(db.Integer, primary_key=True)
	real_name = db.Column(db.String)
	nickname = db.Column(db.String, unique=True)
	email = db.Column(db.String, unique=True)
	password_hash = db.Column(db.String)
	password_set_date = db.Column(db.Date)
	# Metadata
	registration_date = db.Column(db.DateTime)
	last_signin_date = db.Column(db.DateTime)
	last_active_date = db.Column(db.DateTime)
	reputation = db.Column(db.Integer)
	num_messages = db.Column(db.Integer)
	# Flags
	is_active = db.Column(db.Boolean)
	is_new = db.Column(db.Boolean)
	is_blocked = db.Column(db.Boolean)
	is_verified = db.Column(db.Boolean)
	is_superuser = db.Column(db.Boolean)
	is_staff = db.Column(db.Boolean)
	is_moderator = db.Column(db.Boolean)
	# Social data
	website = db.Column(db.String())
	twitter = db.Column(db.String())
	facebook = db.Column(db.String())
	linkedin = db.Column(db.String())
	# Other profile info
	birth_date = db.Column(db.Date)
	is_public_birth_date = db.Column(db.Boolean)
	about = db.Column(db.String())

	# Only one of these will contain a value
	standard_portrait_id = db.Column(db.Integer)
	member_portrait_id = db.Column(db.Integer)
	member_portraits = db.relationship("MemberPortrait", backref="user")

	use_standard_background = db.Column(db.Boolean)
	standard_background_filename = db.Column(db.String())
	background_original = db.Column(db.LargeBinary)
	preferred_language = db.Column(db.Enum(PreferredLanguageType))
	slug = db.Column(db.String())
	from_country = db.Column(db.String(2))
	from_country_name = db.Column(db.String())
	in_country = db.Column(db.String(2))
	in_country_name = db.Column(db.String())
	timezone = db.Column(db.String())
	messages = db.relationship("ConversationMessage", backref="author")

	@classmethod
	def generate_random_password(cls, length=8):
		return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))

	@classmethod
	def is_signed_in(cls):
		return 'user_id' in session

	@classmethod
	def get_signed_in_user(cls):
		if cls.is_signed_in():
			user = User.query.filter_by(id=session['user_id']).first()
			if user is not None:
				db.session.add(user)
				user.last_active_date = datetime.utcnow()
				db.session.commit()
			return user
		else:
			return None

	@classmethod
	def valid_credentials(cls, email, password):
		password_hash = hashlib.sha512(password).hexdigest()
		user = User.query.filter(User.email == email).filter(User.password_hash == password_hash).one_or_none()
		if user:
			return user
		else:
			return False

	@classmethod
	def valid_password(cls, password):
		if len(password) > 7:
			if re.search('[a-z]', password):
				if re.search('[A-Z]', password):
					if re.search('[0-9]', password):
						return True
		return False

	def __init__(self, real_name, email, nickname=None, password=None, registration_date=None, is_active=False, request=None):
		self.real_name = real_name
		self.nickname = nickname
		self.email = email
		self.registration_date = registration_date or datetime.utcnow()
		self.is_active = is_active
		self.is_new = True
		self.is_blocked = False
		self.is_verified = False
		self.is_superuser = False
		self.is_staff = False
		self.reputation = 0
		self.set_password(password)
		self.slug = real_name
		self.use_standard_background = True
		self.standard_background_filename = 'profile_background_1.jpg'
		self.birth_date = '2075-04-01'	# Default value for undefined
		ip = geolite2.lookup(request.headers['X-Real-IP'])
		if ip is not None:
			self.set_in_country(ip.country.upper())
			self.timezone = ip.timezone

	def set_password(self, password=None):
		"""Sets the user password. The plaintext form is kept in the object, but not saved to 
		the database. Because of this, this field will only have a value during password
		changes, and never on objects that have been retrieved from the database.

		Doesn't automatically commit the changes to the database.
		"""
		if password is None:
			password = User.generate_random_password()
		self.password = password # Used to notify the user via email
		self.password_hash = hashlib.sha512(password).hexdigest()
		self.password_set_date = datetime.utcnow()

	def signin(self):
		"""Validation has been done externally, as in the activation form"""
		self.last_signin_date = datetime.utcnow()
		db.session.commit()
		session['user_id'] = self.id

	def send_activation_email(self, url, key):
		message = Message('Your MSX Center account activation')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email]
		message.body = render_template('email/activationemail.txt', activation_url=url, activation_key=key)
		message.html = render_template('email/activationemail.html', activation_url=url, activation_key=key)
		mail.send(message)

	def send_welcome_email(self):
		message = Message('Welcome to MSX Center!')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email]
		message.body = render_template('email/welcomeemail.txt')
		message.html = render_template('email/welcomeemail.html')
		mail.send(message)

	def send_password_reset_email(self, url, key):
		message = Message('Your MSX Center password reset')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email]
		message.body = render_template('email/resetpasswordemail.txt', url=url, key=key)
		message.html = render_template('email/resetpasswordemail.html', url=url, key=key)
		mail.send(message)

	def send_password_reset_success_email(self):
		message = Message('You have reset your MSX Center password')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email]
		message.body = render_template('email/resetpasswordsuccessemail.txt')
		message.html = render_template('email/resetpasswordsuccessemail.html')
		mail.send(message)

	def __repr__(self):
		return "<User(real_name='%s', nickname='%s', email='%s', password_hash='%s', registration_date='%s', is_active='%s')>" % (
			self.real_name, self.nickname, self.email, self.password_hash, self.registration_date, self.is_active)

	def profile_background_url(self):
		return '/static/img/Backgrounds/%s' % self.standard_background_filename

	def profile_photo_url(self, size='standard'):
		res = '512x512' if size == 'standard' else '64x64'
		if self.standard_portrait_id:
			return '/static/img/profile/standard_profile_%s_%s.png' % (self.standard_portrait_id, res)
		elif self.member_portrait_id:
			return url_for('send_member_portrait_image', portrait_id=self.member_portrait_id, size=size)
		else:
			return '/static/img/anonymous_user_%s.png' % ('256x256' if size == 'standard' else '64x64')

	def set_from_country(self, from_country=None):
		self.from_country = from_country
		self.from_country_name = pycountry.countries.get(alpha_2=from_country).name if from_country else None

	def set_in_country(self, in_country=None):
		self.in_country = in_country
		self.in_country_name = pycountry.countries.get(alpha_2=in_country).name if in_country else None

	def get_birth_date(self):
		app.logger.info("User ID %s birth date is %s" % (self.id, self.birth_date))

		result = ''

		if self.birth_date:
			result = self.birth_date

		app.logger.info("Returning %s" % result)
		return result

	def update_reputation(self):

		reputation = 0

		# Comments posted on articles and news items
		for comment in self.comments:
			if comment.score > 0:
				reputation += 1
			elif comment.score < 0:
				reputation -= 1

		# Messages posted in the conversation lounges
		for message in self.messages:
			if message.score > 0:
				reputation += 1
			elif message.score < 0:
				reputation -= 1

		# Update the reputation
		self.reputation = reputation
		db.session.add(self)
		db.session.commit()

	def get_reputation(self):
		"""Return -1 if the user's reputation <-11, 1 if >11, if between -10...10"""
		if abs(self.reputation) > 10:
			return (1, -1)[self.reputation < 0]
		else:
			return 0
