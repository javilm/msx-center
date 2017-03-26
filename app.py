import os, string, hashlib, random, re, enum, socket, json, copy
import jinja_filters
import lxml.html as LH
import pycountry
import pytz
from datetime import datetime
from flask import Flask, request, g, render_template, flash, session, url_for, redirect, abort, session, send_file, jsonify
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from geoip import geolite2
from io import BytesIO
from lxml import etree
from lxml.html.clean import Cleaner
from PIL import Image
from server import run_server
from slugify import slugify
from validate_email import validate_email
from werkzeug.datastructures import FileStorage

# Create and initialize app
app = Flask(__name__)
app.jinja_env.filters['pretty_date'] = jinja_filters.pretty_date
app.jinja_env.filters['supress_none'] = jinja_filters.supress_none
app.jinja_env.auto_reload = True
app.debug = True
app.config.from_object(__name__)
mail = Mail(app)
db = SQLAlchemy(app)
html_cleaner = Cleaner(page_structure=True, links=False)

# Load default config and override config from an environment variable
app.config.update(dict(
	SQLALCHEMY_DATABASE_URI='postgresql://devmsx-centercom:zazuKQ9c@192.168.1.104/devmsx-centercom',
	MAIL_SERVER='192.168.1.200',
	DEFAULT_MAIL_SENDER='javi.lavandeira@msx-center.com',
	SECRET_KEY='e620f0121309a360fc596c481efd895da1c19b1e9358e87a',
	SERVER_NAME='dev.msx-center.com',
	MAX_CONTENT_LENGTH=8*1024*1024
))
app.config.from_envvar('MSXCENTER_SETTINGS', silent=True)

# Create ordered lists of countries and timezones
country_list = sorted(pycountry.countries, key = lambda c: c.name)
timezone_list = sorted(pytz.common_timezones)

############
## MODELS ##
############

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
	messages = db.relationship("ConversationMessage", backref="user")

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

	def __init__(self, real_name, email, nickname=None, password=None, registration_date=None, is_active=False):
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
		self.slug = slugify(slugify(real_name if real_name else nickname))
		self.use_standard_background = True
		self.standard_background_filename = 'profile_background_1.jpg'
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
		message.recipients = [self.email, 'javi@lavandeira.net']
		message.body = render_template('email/activationemail.txt', activation_url=url, activation_key=key)
		message.html = render_template('email/activationemail.html', activation_url=url, activation_key=key)
		mail.send(message)

	def send_welcome_email(self):
		message = Message('Welcome to MSX Center!')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email, 'javi@lavandeira.net']
		message.body = render_template('email/welcomeemail.txt')
		message.html = render_template('email/welcomeemail.html')
		mail.send(message)

	def send_password_reset_email(self, url, key):
		message = Message('Your MSX Center password reset')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email, 'javi@lavandeira.net']
		message.body = render_template('email/resetpasswordemail.txt', url=url, key=key)
		message.html = render_template('email/resetpasswordemail.html', url=url, key=key)
		mail.send(message)

	def send_password_reset_success_email(self):
		message = Message('You have reset your MSX Center password')
		message.sender = 'MSX Center <no-reply@msx-center.com>'
		message.recipients = [self.email, 'javi@lavandeira.net']
		message.body = render_template('email/resetpasswordsuccessemail.txt')
		message.html = render_template('email/resetpasswordsuccessemail.html')
		mail.send(message)

	def __repr__(self):
		return "<User(real_name='%s', short_name='%s', email='%s', password_hash='%s', registration_date='%s', is_active='%s')>" % (
			self.real_name, self.short_name, self.email, self.password_hash, self.registration_date, self.is_active)

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
		while db.session.query(ActivationKey).filter_by(key=key).one_or_none() is not None:
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

class VerificationKey(db.Model):
	"""Used to verify the user's identity on password reset requests"""
	__tablename__ = 'verification_keys'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	user = db.relationship('User', backref=db.backref('verification_users', lazy='dynamic'))
	key = db.Column(db.String(16), unique=True)
	creation_date = db.Column(db.DateTime)

	@classmethod
	def generate(cls, length=12):
		key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))
		# Make sure the key is unique
		while db.session.query(VerificationKey).filter_by(key=key).one_or_none() is not None:
			key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))
		return key

	def __init__(self, user, key=None, creation_date=None):
		self.user = user	# Already fetched from the database in the functions that use this
		if key is None:
			key = VerificationKey.generate()
		self.key = key
		if creation_date is None:
			creation_date = datetime.utcnow()
		self.creation_date = creation_date

	def __repr__(self):
		return "<VerificationKey(user='%s', key='%s', creation_date='%s')>" % (
			self.user.real_name, self.key, self.creation_date)

class StoredImage(db.Model):
	__tablename__ = 'stored_images'
	
	id = db.Column(db.Integer, primary_key=True)
	md5_hash = db.Column(db.String(32), unique=True)
	mime_type = db.Column(db.String())
	format = db.Column(db.String())
	width = db.Column(db.Integer)
	height = db.Column(db.Integer)
	data = db.Column(db.LargeBinary)
	datetime_created = db.Column(db.DateTime)
	num_views = db.Column(db.Integer)
	original_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	
	def __init__(self, file=None, datauri=None, original=None):
		if file:
			# Create an image from a file or an instance of Werkzeug's FileStorage class
			if file.__class__ == FileStorage:
				self.data = file.stream.read()
			else:
				self.data = file.getvalue()
			
			self.original_id = None
			
		elif datauri:
			# Read the image data from a Base64-encoded stream in the format:
			# 'data:image/png;base64,iVBORw0KGgo...'
			self.data = datauri.split(',')[1].decode('base64')

			self.original_id = None
			
		elif original:
			# Create a new image by duplicating one from the database
			self.data = original.data
			self.original_id = original.id
		
		else:
			return None

		# Check that the data represents a valid image
		try:
			tmp = Image.open(BytesIO(self.data))
		except IOError:
			return None
			
		# The image was opened without errors
		self.format = tmp.format
		self.mime_type = Image.MIME[tmp.format]
		self.width = tmp.width
		self.height = tmp.height
		self.datetime_created = datetime.utcnow()
		self.num_views = 0
		self.update_md5()
		
	@classmethod
	def from_file(cls, file):
		return cls(file=file)
		
	@classmethod
	def from_datauri(cls, datauri):
		return cls(datauri=datauri)
		
	@classmethod
	def from_original(cls, original):
		return cls(original=original)

	@classmethod
	def from_database_md5(cls, md5_hash):
		"""Returns the image in the database with the given MD5 hash, or None if it doesn't exist"""
		return StoredImage.query.filter_by(md5_hash=md5_hash).first()
		
	def make_square(self):
		"""If the image isn't square then crop it and keep only the central square part."""
		
		# Read image in memory
		original = Image.open(BytesIO(self.data))

		# Do nothing if the image is already square
		if self.width == self.height:
			return True
		
		# Crop if not square
		if self.width > self.height:
			box = (
				(self.width - self.height)/2,
				0,
				(self.width + self.height)/2,
				self.height
			)
		elif self.height > self.width:
			box = (
				0,
				(self.height - self.width)/2,
				self.width,
				(self.height + self.width)/2
			)
		square_image = original.crop(box)

		# Update the data and size values
		tmp_stream = BytesIO()
		square_image.save(tmp_stream, string.upper(self.format))
		self.data = tmp_stream.getvalue()
		self.width = square_image.width
		self.height = square_image.height
		self.update_md5()
		
	def	fit_within(self, width, height):
		"""Make the image fit within (width, height). Replaces the original data."""

		# Read image in memory
		original = Image.open(BytesIO(self.data))
		
		# If the image doesn't fit within (witdth, height) then resample it
		if original.size[0] > width or original.size[1] > height:
			original.thumbnail((width, height), resample=Image.LANCZOS)
			
		# Store the resampled data
		resampled_stream = BytesIO()
		original.save(resampled_stream, string.upper(self.format))
		self.data = resampled_stream.getvalue()
		self.width = original.width
		self.height = original.height
		self.update_md5()

	def update_md5(self):
		self.md5_hash = hashlib.md5(self.data).hexdigest()

class MemberPortrait(db.Model):
	__tablename__ = 'member_portraits'
	
	id = db.Column(db.Integer, primary_key=True)
	original_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	standard_portrait_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	thumbnail_portrait_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	
	def __init__(self, src_file):
	
		# Store the original image
		original = StoredImage.from_file(src_file)
		
		if original:	# Will be None if the original couldn't be imported
			db.session.add(original)
			db.session.commit()
			self.original_id = original.id
		
			# Create standard portrait
			standard_portrait = StoredImage.from_original(original)
			standard_portrait.make_square()
			standard_portrait.fit_within(256, 256)
			
			# Create portrait thumbnail
			thumbnail_portrait = StoredImage.from_original(original)
			thumbnail_portrait.make_square()
			thumbnail_portrait.fit_within(64, 64)

			# Save the new portraits in the database and store the IDs in the instance
			db.session.add(standard_portrait)
			db.session.add(thumbnail_portrait)
			db.session.commit()
			self.standard_portrait_id = standard_portrait.id
			self.thumbnail_portrait_id = thumbnail_portrait.id
			
		else:
			return None

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
	threads = db.relationship("ConversationThread", backref="lounge")

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

	def __init__(self, name_en, desc_en, name_ja=None, name_es=None, name_nl=None, name_pt=None, name_kr=None, desc_ja=None, desc_es=None, desc_nl=None, desc_pt=None, desc_kr=None):

		# Lounge name in several languages
		self.name_en = name_en
		self.name_ja = name_ja
		self.name_es = name_es
		self.name_nl = name_nl
		self.name_pt = name_pt
		self.name_kr = name_kr

		# Lounge description in several languages
		self.desc_en = desc_en
		self.desc_ja = desc_ja
		self.desc_es = desc_es
		self.desc_nl = desc_nl
		self.desc_pt = desc_pt
		self.desc_kr = desc_kr

		# Flags and metadata
		self.allows_anonymous = False
		self.allows_nicknames = False
		self.allows_unverified = False
		self.allows_new = False
		self.allows_bad_reputation = False
		self.staff_only = True
		self.is_visible = True
		self.is_readonly = False
		self.num_threads = 99
		self.priority = 10
		self.color_class = 'success'
		self.slug = slugify(unicode(name_en))

	def add_thread(self, thread):
		thread.lounge_id = self.id
		db.session.add(self)
		db.session.add(thread)
		self.num_threads = db.session.query(ConversationThread).filter_by(lounge_id=self.id).count()	# Recount to make it accurate
		db.session.commit()

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
		self.num_messages = db.session.query(ConversationMessage).filter_by(thread_id=self.id).count()	# Recount to make it accurate instead of just num_messages += 1
		self.last_post_date = datetime.utcnow()
		db.session.commit()

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

class NewsCategory(db.Model):
	__tablename__ = 'news_categories'

	id = db.Column(db.Integer, primary_key=True)
	name_en = db.Column(db.String())
	name_ja = db.Column(db.String())
	name_nl = db.Column(db.String())
	name_es = db.Column(db.String())
	name_pt = db.Column(db.String())
	name_kr = db.Column(db.String())

	def __init__(self, name_en=None, name_ja=None, name_nl=None, name_es=None, name_pt=None, name_kr=None):
		self.name_en = html_cleaner.clean_html(name_en) if name_en else None
		self.name_ja = html_cleaner.clean_html(name_ja) if name_ja else None
		self.name_nl = html_cleaner.clean_html(name_nl) if name_nl else None
		self.name_es = html_cleaner.clean_html(name_es) if name_es else None
		self.name_pt = html_cleaner.clean_html(name_pt) if name_pt else None
		self.name_kr = html_cleaner.clean_html(name_kr) if name_kr else None

class NewsItem(db.Model):
	__tablename__ = 'news_items'

	id = db.Column(db.Integer, primary_key=True)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	headline_en = db.Column(db.String())
	headline_ja = db.Column(db.String())
	headline_nl = db.Column(db.String())
	headline_es = db.Column(db.String())
	headline_pt = db.Column(db.String())
	headline_kr = db.Column(db.String())
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
	header_image_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	date_created = db.Column(db.DateTime)
	date_published = db.Column(db.DateTime)
	is_published = db.Column(db.Boolean)
	is_hidden = db.Column(db.Boolean)
	is_feature = db.Column(db.Boolean)	# Feature items are eligible to appear in the front page
	is_archived = db.Column(db.Boolean)	# Archived items do not accept new comments
	allows_comments = db.Column(db.Boolean)
	url = db.Column(db.String())
	num_comments = db.Column(db.Integer)
	score = db.Column(db.Integer)
	
	def __init__(self, author_id, headline_en=None, headline_ja=None, headline_nl=None, headline_es=None, headline_pt=None, headline_kr=None, subhead_en=None, subhead_ja=None, subhead_nl=None, subhead_es=None, subhead_pt=None, subhead_kr=None, body_en=None, body_ja=None, body_nl=None, body_es=None, body_pt=None, body_kr=None, is_draft_en=True, is_draft_ja=True, is_draft_nl=True, is_draft_es=True, is_draft_pt=True, is_draft_kr=True, header_image=None, date_published=None, is_published=False, is_hidden=False, is_feature=False, is_archived=False, allows_comments=True, url=None):
		self.author_id = author_id
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
		self.header_image_id = header_image.id if header_image else None
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

class ExternalLink(db.Model):
	__tablename__ = 'external_links'

	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String())
	num_visits = db.Column(db.Integer)
	
	def __init__(self, url=None):
		self.url = url
		self.num_visits = 0

#######################
## APPLICATION SETUP ##
#######################
    
# Create test user
@app.before_first_request
def create_database_tables():
	db.create_all()

	# Delete ConversationLounges if there are any
	ConversationMessage.query.delete()
	ConversationThread.query.delete()
	ConversationLounge.query.delete()

	# Add initial conversation lounges
	l1 = ConversationLounge('General conversation', "This lounge is for general conversation. You're welcome to discuss anything that would be offtopic in the other lounges.")
	l1.priority = 10
	l1.color_class = 'info'
	l1.allows_anonymous = False
	l1.allows_nicknames = False
	l1.allows_unverified = True
	l1.allows_bad_reputation = False
	l1.allows_new = True
	l1.staff_only = False
	db.session.add(l1)

	l2 = ConversationLounge('Software and hardware development', "Conversations about development on or for MSX (and/or other retro platforms). Conversations about cross-development using modern tools and platforms is also very welcome.")
	l2.priority = 20
	l2.color_class = 'info'
	l2.allows_anonymous = False
	l2.allows_nicknames = True
	l2.allows_unverified = True
	l2.allows_bad_reputation = False
	l2.allows_new = True
	l2.staff_only = False
	db.session.add(l2)

	l3 = ConversationLounge('Music and graphics', "The lounge for our artists. Talk about graphics, music, sound, and the tools and techniques to create them.")
	l3.priority = 30
	l3.color_class = 'info'
	l3.allows_anonymous = False
	l3.allows_nicknames = True
	l3.allows_unverified = True
	l3.allows_bad_reputation = False
	l3.allows_new = True
	l3.staff_only = False
	db.session.add(l3)

	l4 = ConversationLounge('Emulation', "Running emulated systems in modern hardware and conversations about the emulators themselves, rather than the systems being emulated.")
	l4.priority = 40
	l4.color_class = 'info'
	l4.allows_anonymous = False
	l4.allows_nicknames = True
	l4.allows_unverified = True
	l4.allows_bad_reputation = False
	l4.allows_new = True
	l4.staff_only = False
	db.session.add(l4)

	l5 = ConversationLounge('Trading and collecting', "Our marketplace. Buy and sell stuff!")
	l5.priority = 50
	l5.color_class = 'info'
	l5.allows_anonymous = False
	l5.allows_nicknames = False
	l5.allows_unverified = False
	l5.allows_bad_reputation = False
	l5.allows_new = False
	l5.staff_only = False
	db.session.add(l5)

	l6 = ConversationLounge('MSX Center help and support', "Feedback and questions about our website, help, troubleshooting, suggestions, etc.")
	l6.priority = 60
	l6.color_class = 'success'
	l6.allows_anonymous = True
	l6.allows_nicknames = True
	l6.allows_unverified = True
	l6.allows_bad_reputation = True
	l6.allows_new = True
	l6.staff_only = False
	db.session.add(l6)

	l7 = ConversationLounge('Administration', "Lounge for MSX Center staff. Maintenance of the site, developmeint, bugfixes, financing, organization, etc.")
	l7.priority = 70
	l7.color_class = 'danger'
	l7.allows_anonymous = False
	l7.allows_nicknames = False
	l7.allows_unverified = False
	l7.allows_bad_reputation = False
	l7.allows_new = False
	l7.staff_only = True
	db.session.add(l7)

	db.session.commit()


#######################
## Support functions ##
#######################

def redirect_to_next():
	if 'next' in session:
		url = session['next']
	else:
		url = url_for('page_main')
	return redirect(url)

def get_host_by_ip(ip):
	try:
		data = socket.gethostbyaddr(ip)
		host = repr(data[0])
		return host
	except Exception:
		return None

########################
## APPLICATION ROUTES ##
########################

@app.route('/')
def page_main():
	session['next'] = url_for('page_main')

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	return render_template('frontpage.html', user=user)

########################
## SIGNIN AND SIGNOUT ##
########################

@app.route('/signin', methods=['GET', 'POST'])
def page_signin():
	# If the user is already signed in but comes here anyway, redirect to the front page
	if User.is_signed_in():
		return redirect_to_next()
	if request.method == 'POST':
		user = User.valid_credentials(request.form['signin-email'], request.form['signin-password'])
		if user:
			user.signin()
			return redirect_to_next()
		else:
			flash('Invalid email address or password')
			return redirect(url_for('page_signin'))
	else:
		return render_template('signin.html')

@app.route('/signout')
def page_signout():
	session.pop('user_id', None)
	return redirect_to_next()

###################################
## SIGNUP AND ACCOUNT ACTIVATION ##
###################################

# Account creation process:
#
# 1: Create account, generate verification key and send verification email
#
# 1.1) GET /createaccount: Enter real name and email address
# 1.2) POST /createaccount: Generate verification key and send verification email
#		Display message asking to check the email account

@app.route('/createaccount', methods=['GET', 'POST'])
def page_createaccount():
	# If the user is already signed in but comes here anyway, redirect to the front page
	if User.is_signed_in():
		return redirect_to_next()

	template_options = {'invalid_realname': False, 'invalid_email': False}

	if request.method == 'GET':
		return render_template('createaccount.html', **template_options)
	else:
		# request.method == 'POST'
		submitted_email = request.form['signup_email'].lower()

		template_options['signuprealname'] = request.form['signup_realname']
		template_options['signupemail'] = submitted_email

		# Validate the real name
		if not string.strip(request.form['signup_realname']):
			template_options['invalid_realname'] = True
			template_options['error_realname'] = 'You cannot leave your name empty'

		# Validate the email address		
		# Check whether it's already in the database
		if db.session.query(User).filter_by(email=submitted_email).first() is not None:
			template_options['invalid_email'] = True
			template_options['error_email'] = "That email address is already registered"
		# Check whether the email address is empty
		elif not string.strip(request.form['signup_email']):
			template_options['invalid_email'] = True
			template_options['error_email'] = "Your email address can't be empty"
		# Check whether the domain in the email address exists
		elif not validate_email(submitted_email, check_mx=True):
			template_options['invalid_email'] = True
			template_options['error_email'] = 'The domain in your email address is invalid'

		# Check whether there were any errors
		if template_options['invalid_realname'] or template_options['invalid_email']:
			flash("The information you submitted wasn't valid. Check the error(s) below.")
			return render_template('createaccount.html', **template_options)
		else:
			# At this point create the activation key and the inactive user, then send the activation email
			user = User(real_name=request.form['signup_realname'], email=submitted_email)
			# Check that the activation key isn't duplicated (unlikely, but possible)
			key = ActivationKey(user)
			db.session.add(user)
			db.session.add(key)
			db.session.commit()
			app.logger.info("New user registered: %s <%s>" % (user.real_name, user.email))

			# Send activation email
			activation_url = url_for('page_activate', _external=True, key=key.key)
			user.send_activation_email(activation_url, key.key)

			# Present the thank you screen
			return render_template('createaccount-thankyou.html', email_address=submitted_email)

# 2: User clicks on the link or accesses the verification page manually
#
# 2.1) GET /activate
#	If the request doesn't contain a "key" parameter, then render the form to
#	ask the user to enter the activation key. The form will GET its own URL
#	with the "key" parameter entered by the user.
#	If the request contains a "key" parameter, then search the database for this
#	key. If it doesn't exist, or has expired, render the form again with the
#	appropriate error message.
#	If the key exists, display the form to set the user's password. The form 
#	will POST to its own URL with the activation key's database ID in the
#	'key_id' session variable, the password in the 'password' parameter, and
#	the password confirmation in the 'passwordconfirmation' parameter.
# 2.2) POST /activate
#	Check the "key_id" session variable to check again that the activation key is
#	valid (should be unless someone is messing with the session). If the key is
#	invalid then render the form to ask the user for the activation key again,
#	with the appropriate error message.
#	Check that the password follows the requirements. If it doesn't, render the
#	form again with the appropriate error message.
#	If the password meets the requirements:
#	- Set the user password
#	- Set the user's activation date/time
#	- Log the user in
#	- Redirect to the main page

@app.route('/activate', methods=['GET', 'POST'])
def page_activate():
	# If the user is already signed in but comes here anyway, redirect to the front page
	if User.is_signed_in():
		return redirect_to_next()

	if request.method == 'GET':
		if 'key' in request.args:
			# Try and get the key from the database
			key = db.session.query(ActivationKey).filter_by(key=request.args['key']).first()
			if key is not None:
				# GET, with a valid activation key
				session['key_id'] = key.id
				user = db.session.query(User).filter_by(id=key.user_id).first()
				return render_template('activate-setpassword.html', email=user.email)
			else:
				# GET, 'key' argument is in the URL, but not in the database
				return render_template('activate-getkey.html', invalid_key=True, key=request.args['key'])
		else:
			# GET, but no 'key' argument in the URL
			return render_template('activate-getkey.html')
	else:
		# request.method == 'POST'

		# First confirm that there's a session variable with the key (in case the user POSTs here directly)
		if 'key_id' not in session:
			# No 'key_id' in the session. The user POSTed directly to this form
			return render_template('activate-getkey.html')
		else:
			key = db.session.query(ActivationKey).filter_by(id=session['key_id']).first()
			if key is None:
				# There is an invalid key_id in the session, remove it and ask for another
				session.pop('key_id', None)
				return render_template('activate-getkey.html')

		# At this point 'key' contains a valid activation key

		# Validate the password (don't rely on the Javascript validation on the form,
		# because that's only client-side and can be disabled by the user)
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if request.form['password'] != request.form['passwordconfirm']:
			num_validation_errors += 1
			error_messages.append("The passwords you entered don't match")

		# Check that the password passes validation
		if not User.valid_password(request.form['password']):
			num_validation_errors += 1
			error_messages.append("The password doesn't meet all the requirements below")

		# If there were validation errors then display the form again
		if num_validation_errors:
			return render_template('activate-setpassword.html', num_errors=num_validation_errors, error_messages=error_messages)
		else:
			#  Get the User from the database
			user = db.session.query(User).filter_by(id=key.user_id).first()

			user.set_password(request.form['password'])		# Set the user password
			user.is_active = True							# Activate the user
			user.signin()									# Sign in the user
			db.session.delete(key)							# Delete the activation key
			db.session.commit()								# Save changes

			app.logger.info("User activated his account: %s <%s>" % (user.real_name, user.email))
			user.send_welcome_email()

			# Redirect to the main page
			return redirect(url_for('page_main'))

##############################
## RESET FORGOTTEN PASSWORD ##
##############################

# Password reset. This is very similar to the account activation function.
#
# 1: Request password reset, generate verification key and send verification email
#
# 1.1) GET /resetpassword: Enter email address
# 1.2) GET /resetpassword?email=XXXXXX: Generate verification key and send verification email
#		Display message asking to check the email account

# 2.1) GET /verifypasswordreset
#	If the request doesn't contain a "key" parameter, then render the form to
#	ask the user to enter the activation key. The form will GET its own URL
#	with the "key" parameter entered by the user.
#	If the request contains a "key" parameter, then search the database for this
#	key. If it doesn't exist, or has expired, render the form again with the
#	appropriate error message.
#	If the key exists, display the form to set the user's password. The form 
#	will POST to its own URL with the activation key's database ID in the
#	'key_id' session variable, the password in the 'password' parameter, and
#	the password confirmation in the 'passwordconfirmation' parameter.
# 2.2) POST /verifypasswordreset
#	Check the "key_id" session variable to check again that the activation key is
#	valid (should be unless someone is messing with the session). If the key is
#	invalid then render the form to ask the user for the activation key again,
#	with the appropriate error message.
#	Check that the password follows the requirements. If it doesn't, render the
#	form again with the appropriate error message.
#	If the password meets the requirements:
#	- Set the user password
#	- Set the user's activation date/time
#	- Log the user in
#	- Redirect to the main page
@app.route('/resetpassword', methods=['GET'])
def page_resetpassword():
	# If the user is already signed in but comes here anyway, redirect to the front page
	if User.is_signed_in():
		return redirect_to_next()

	if 'email' in request.args:
		# Try and get the user from the database
		user = db.session.query(User).filter_by(email=request.args['email']).one_or_none()
		if user is not None:
			# GET, with a valid email address

			# Generate a key and make sure it's not duplicated
			key = VerificationKey(user)
			db.session.add(key)
			db.session.commit()

			# Send verification email
			verification_url = url_for('page_verifypasswordreset', _external=True)
			user.send_password_reset_email(verification_url, key.key)

		return render_template('resetpassword-received.html', email=request.args['email'])
	else:
		# GET, but no 'email' argument in the URL
		return render_template('resetpassword-getemail.html')

@app.route('/verifypasswordreset', methods=['GET', 'POST'])
def page_verifypasswordreset():
	# If the user is already signed in but comes here anyway, redirect to the front page
	if User.is_signed_in():
		return redirectto_next()

	if request.method == 'GET':
		if 'key' in request.args:
			# Try and get the key from the database
			key = db.session.query(VerificationKey).filter_by(key=request.args['key']).first()
			if key is not None:
				# GET, with a valid activation key
				session['key_id'] = key.id
				user = db.session.query(User).filter_by(id=key.user_id).first()
				return render_template('resetpassword-setpassword.html', email=user.email)
			else:
				# GET, 'key' argument is in the URL, but not in the database
				return render_template('resetpassword-getemail.html', invalid_key=True, key=request.args['key'])
		else:
			# GET, but no 'key' argument in the URL
			return render_template('resetpassword-getemail.html')
	else:
		# request.method == 'POST'

		# First confirm that there's a session variable with the key (in case the user POSTs here directly)
		if 'key_id' not in session:
			# No 'key_id' in the session. The user POSTed directly to this form
			return render_template('resetpassword-getemail.html')
		else:
			key = db.session.query(VerificationKey).filter_by(id=session['key_id']).first()
			if key is None:
				# There is an invalid key_id in the session, remove it and ask for another
				session.pop('key_id', None)
				return render_template('resetpassword-getemail.html')

		# At this point 'key' contains a valid verification key

		# Validate the password (don't rely on the Javascript validation on the form,
		# because that's only client-side and can be disabled by the user)
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if request.form['password'] != request.form['passwordconfirm']:
			num_validation_errors += 1
			error_messages.append("The passwords you entered don't match")

		# Check that the password passes validation
		if not User.valid_password(request.form['password']):
			num_validation_errors += 1
			error_messages.append("The password doesn't meet all the requirements below")

		# If there were validation errors then display the form again
		if num_validation_errors:
			return render_template('resetpassword-setpassword.html', num_errors=num_validation_errors, error_messages=error_messages)
		else:
			#  Get the User from the database
			user = db.session.query(User).filter_by(id=key.user_id).first()

			user.set_password(request.form['password'])		# Set the user password
			user.signin()									# Sign in the user
			db.session.delete(key)							# Delete the activation key
			db.session.commit()								# Save changes

			app.logger.info("User %s <%s> changed his password to %s" % (user.real_name, user.email, request.form['password']))
			user.send_password_reset_success_email()

			# Redirect to the main page
			return redirect(url_for('page_main'))

##########################
## CONVERSATION LOUNGES ##
##########################

@app.route('/lounges', methods=['GET'])
def page_lounges_list():
	session['next'] = url_for('page_lounges_list')
	user = None
	signed_in = False
	if User.is_signed_in():
		user = User.get_signed_in_user()
		if user is None:
			# Invalid user ID in session. Remove it from the session and ask the user to sign in again
			session.pop('user_id', None)
			flash('You were signed out. Please sign in again.')
			return redirect(url_for('page_signin'))
		else:
			signed_in = True

	# Get all the conversation lounges
	lounges = ConversationLounge.query.order_by(ConversationLounge.priority)

	# Get the latest 5 threads for each lounge
	threads = {}
	for lounge in lounges:
		threads[lounge.id] = ConversationThread.query.filter(ConversationThread.lounge_id == lounge.id).order_by(ConversationThread.last_post_date).limit(5).all()

	return render_template('lounges/lounges-list.html', lounges=lounges, threads=threads, signed_in=signed_in, user=user)

@app.route('/lounge/<int:lounge_id>/new', methods=['GET', 'POST'])
def page_lounge_post(lounge_id):
	session['next'] = url_for('page_lounge_post', lounge_id=lounge_id)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if request.method == 'GET':
		# Accessed the URL using the GET method

		# Get the ConversationLounge details
		lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

		# Return a 404 error if the lounge doesn't exist
		if lounge is None:
			abort(404)

		# Validate the user's permissions (the user may be denied posting based on more than one criteria, but
		# the template will only display the first that matches)
		user_errors = ConversationLounge.get_permission_errors(user, lounge)

		template_options = {
			'lounge': lounge,
			'user': user,
			'errors': user_errors
		}

		return render_template('lounges/lounges-startconversation.html', **template_options)
	else:
		# Accessed the URL using the POST method, usually via AJAX

		# Get all the request parameters in an ImmutableMultiDict
		dict = request.form
		if len(dict):
			# Parameters: title, post_as, message
			# lounge_id comes from the URI
			# Possible errors:
			#	- lounge does not exist
			#	- failed validation (empty title, anon user in non-anon lounge, etc)
			#	- empty message
			lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

			# Validate the user's permissions to post
			user_errors = {}
			if user is None:
				# Anonymous user is only allowed to post if the lounge allows anonymous posts, very easy to check
				if lounge.allows_anonymous:
					post_as = 'ANON'
				else:
					user_errors['anonymous'] = True
			# At this point the user is not anonymous, so we have to check the user's status (blocked, rep, etc) and 
			# the lounge's access permissions to see whether he's allowed to post
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
			# At this point the user is allowed to post. If the user requests to post as anonymous or using a nickname
			# then check whether the lounge allows it.
			elif dict['post_as'] == '3' and lounge.allows_anonymous:
				post_as = 'ANON'
			elif dict['post_as'] == '2' and lounge.allows_nicknames:
				post_as = 'NICKNAME'
			else:
				post_as = 'REALNAME'

			if not user_errors:
				thread = ConversationThread(title_en=dict['title'])
				lounge.add_thread(thread)
				message = ConversationMessage(user, post_as, dict['message'])
				thread.add_message(message)
				return json.dumps({
					'status': 200,
					'url': url_for('page_thread', thread_id=thread.id, slug=thread.slug)
				})
			else:
				return json.dumps(user_errors, sort_keys=True, indent=4)
		else:
			# This is an error, nothing was submitted. Often the case when bots attack the site.
			return "The input dictionary was empty"

@app.route('/lounges/<int:lounge_id>/<string:slug>/list', methods=['GET'])
def page_lounge(lounge_id, slug):
	session['next'] = url_for('page_lounge', lounge_id=lounge_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	# Get the ConversationLounge details
	lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

	# Return a 404 error if the lounge doesn't exist
	if lounge is None:
		abort(404)
	
	# Render the template
	template_options = {
		'user': user,
		'lounge': lounge
	}

	return render_template('lounges/lounge-thread-list.html', **template_options)

@app.route('/lounges/thread/<int:thread_id>/<string:slug>', methods=['GET', 'POST'])
def page_thread(thread_id, slug):
	session['next'] = url_for('page_thread', thread_id=thread_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()
	thread = ConversationThread.query.filter_by(id=thread_id).first()

	if thread is None:
		abort(404)

	if request.method == 'GET':

		################################################
		## GET: Present the thread and the reply form ##
		################################################

		# Update the number of views for this thread
		db.session.add(thread)
		thread.num_views += 1
		db.session.commit()

		# Check the user's permission to post in the thread
		user_errors = {}
		if user is None:
			if not thread.lounge.allows_anonymous:
				user_errors['anonymous'] = True
		elif user.is_blocked:
			user_errors['blocked'] = True
		elif user.is_new and not thread.lounge.allows_new:
			user_errors['new'] = True
		elif not user.is_verified and not thread.lounge.allows_unverified:
			user_errors['unverified'] = True
		elif not user.is_staff and thread.lounge.staff_only:
			user_errors['not_staff'] = True
		elif user.reputation < 0 and not thread.lounge.allows_bad_reputation:
			user_errors['bad_reputation'] = True

		# Render the template
		template_options = {
			'user': user,
			'thread': thread,
			'lounge': thread.lounge,
			'errors': user_errors
		}

		return render_template('lounges/lounges-thread.html', **template_options)

	else:

		#############################
		## POST: Process the reply ##
		#############################

		# Get all the request parameters in an ImmutableMultiDict
		dict = request.form

		if len(dict):
			# Parameters: post_as, message
			# lounge_id comes from the URI
			# Possible errors:
			#	- lounge does not exist
			#	- failed validation (empty message, anon user in non-anon lounge, etc)
			lounge = thread.lounge

			# Validate the user's permissions to post
			user_errors = {}
			if user is None:
				# Anonymous user is only allowed to post if the lounge allows anonymous posts, very easy to check
				if lounge.allows_anonymous:
					post_as = 'ANON'
				else:
					user_errors['anonymous'] = True
			# At this point the user is not anonymous, so we have to check the user's status (blocked, rep, etc) and 
			# the lounge's access permissions to see whether he's allowed to post
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
			# At this point the user is allowed to post. If the user requests to post as anonymous or using a nickname
			# then check whether the lounge allows it.
			elif dict['post_as'] == '3' and lounge.allows_anonymous:
				post_as = 'ANON'
			elif dict['post_as'] == '2' and lounge.allows_nicknames:
				post_as = 'NICKNAME'
			else:
				post_as = 'REALNAME'

			if not user_errors:
				message = ConversationMessage(user, post_as, body_en=dict['message'])
				thread.add_message(message)
				return json.dumps({
					'status': 200,
					'url': url_for('page_thread', thread_id=thread.id, slug=thread.slug)
				})
			else:
				return json.dumps(user_errors, sort_keys=True, indent=4)
		else:
			# This is an error, nothing was submitted. Often the case when bots attack the site.
			return "The input dictionary was empty"

@app.route('/image/<int:image_id>/<string:dummy_filename>', methods=['GET'])
def send_image(image_id, dummy_filename):
	image = StoredImage.query.filter_by(id=image_id).first()
	if image is not None:
		db.session.add(image)
		image.num_views += 1
		db.session.commit()

		byte_io = BytesIO(image.data)
		return send_file(byte_io, mimetype=image.mime_type)
	else:
		abort(404)

####################
## MEMBER PROFILE ##
####################

@app.route('/member/<int:member_id>/<string:slug>')
def page_member(member_id, slug):
	# Note: in the context of this route, the "user" is the logged in user, and the "member" is
	# the user whose profile is being visited. They may or may not be the same.
	session['next'] = url_for('page_member', member_id=member_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	# Get the visited member
	member = User.query.filter_by(id=member_id).first()

	if member is None:
		abort(404)

	return render_template('member/member_view.html', user=user, member=member)

@app.route('/member/portrait/<int:portrait_id>/<string:size>')
def send_member_portrait_image(portrait_id, size):
	# If "size" isn't either 'standard' or 'small' then return a 404
	if size != 'standard' and size != 'small':
		abort(404)

	portrait = MemberPortrait.query.filter_by(id=portrait_id).first()
	if portrait is not None:
		if size == 'standard':
			image = StoredImage.query.filter_by(id=portrait.standard_portrait_id).first()
		elif size == 'small':
			image = StoredImage.query.filter_by(id=portrait.thumbnail_portrait_id).first()

		byte_io = BytesIO(image.data)
		return send_file(byte_io, mimetype=image.mime_type)

	else:
		abort(404)

@app.route('/member/edit/background', methods=['GET', 'POST'])
def page_member_edit_background():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	if request.method == 'GET':
		return render_template('member/member_edit_background.html', user=user)
	else:
		# Request method is POST
		error_message = None
		background_num = int(request.form['standard_background_number'])
		if background_num < 1 or background_num > 6:
			error_message = "The background you selected isn't available. Please try again."
			return render_template('member/member_edit_background.html', user=user, )
		else:
			user.standard_background_filename = 'profile_background_%s.jpg' % background_num
			db.session.add(user)
			db.session.commit()
			return redirect(url_for('page_member', member_id=user.id, slug=user.slug))

@app.route('/member/edit/photo', methods=['GET', 'POST'])
def page_member_edit_photo():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	if request.method == 'GET':
		return render_template('member/member_edit_photo.html', user=user, errors=None)
	else:
		# Request method is POST

		# First update the portrait selection
		if request.form['standard_portrait_number'] is not None:
			user.standard_portrait_id = int(request.form['standard_portrait_number'])
		else:
			user.standard_portrait_id = None
		if request.form['member_portrait_number'] is not None:
			user.member_portrait_id = int(request.form['member_portrait_number'])
		else:
			user.member_portrait_id = None
		db.session.add(user)

		# Then process the upload, if there is one
		upload_handled = False
		if 'uploaded_photo' in request.files:
			src_file = request.files['uploaded_photo']
			if src_file.filename:
				portrait = MemberPortrait(src_file)
				if portrait:
					portrait.user_id = user.id
					db.session.add(portrait)
					db.session.commit()
					user.member_portrait_id = portrait.id
					upload_handled = True
				else:
					errors = "The file you uploaded doesn't seem to be a valid image. Please try a different file."
					return render_template('member/member_edit_photo.html', user=user, errors=errors)
			# else there was no file upload

		# Save the changes in the database
		db.session.commit()

		# Finally, redirect the user back to his profile view (if there were no uploads) or back to the portrait page (if there were)
		if upload_handled:
			return render_template('member/member_edit_photo.html', user=user, errors=None)
		else:
			return redirect(url_for('page_member', member_id=user.id, slug=user.slug))
		
@app.route('/member/edit/password', methods=['GET', 'POST'])
def page_member_edit_password():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	if request.method == 'GET':
		return render_template('member/member_edit_password.html', user=user, errors=None)
	else:
		# Method is POST, user trying to change the passwordd
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if request.form['new_pass'] != request.form['new_pass_conf']:
			num_validation_errors += 1
			error_messages.append("The passwords you entered don't match")

		# Check that the new password isn't the same as the current password
		if request.form['new_pass'] == request.form['current_pass']:
			num_validation_errors += 1
			error_messages.append("The new password can't be the same as your current password.")

		# Check that the password passes validation
		if not User.valid_password(request.form['new_pass']):
			num_validation_errors += 1
			error_messages.append("The password doesn't meet all the requirements.")

		# Check that the current password is correct
		if not User.valid_credentials(user.email, request.form['current_pass']):
			num_validation_errors += 1
			error_messages.append("The current password that you entered isn't the one on record.")

		if num_validation_errors:
			return render_template('member/member_edit_password.html', user=user, errors=error_messages)
		else:
			user.set_password(request.form['new_pass'])
			db.session.add(user)
			db.session.commit()
			# Redirect instead of rendering the template to avoid resubmission of the form data
			return redirect(url_for('page_member_edit_password_success'))
		
@app.route('/member/edit/password/success', methods=['GET'])
def page_member_edit_password_success():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	return render_template('member/member_edit_password_success.html', user=user)

@app.route('/member/edit/profile', methods=['GET', 'POST'])
def page_member_edit_profile():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	if request.method == 'GET':
		return render_template('member/member_edit_profile.html', user=user, country_list=country_list, timezone_list=timezone_list)
	else:
		# Method is POST, user trying to change the passwordd
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if not request.form['real_name'] and not request.form['nickname']:
			num_validation_errors += 1
			error_messages.append("You can't leave blank both your real name and your nickname.")

		if num_validation_errors:
			return render_template('member/member_edit_profile.html', user=user, country_list=country_list, timezone_list=timezone_list, errors=error_messages)
		else:
			user.real_name = request.form['real_name']
			user.nickname = request.form['nickname']
			user.birth_date = request.form['birthdate']
			if 'is_public_birthdate' in request.form:
				user.is_public_birth_date = True
			else: 
				user.is_public_birth_date = False
			user.about = request.form['about']
			user.set_from_country(request.form['from_country'])
			user.set_in_country(request.form['in_country'])
			user.timezone = request.form['timezone']
			user.preferred_language = request.form['language'].upper()
			user.website = request.form['website']
			user.facebook = request.form['facebook']
			user.linkedin = request.form['linkedin']
			user.twitter = request.form['twitter']
			user.slug = slugify(slugify(request.form['real_name'] if request.form['real_name'] else request.form['nickname']))
			db.session.add(user)
			db.session.commit()
			# Redirect instead of rendering template to avoid double-posting on page reload
			return redirect(url_for('page_member_edit_profile_success'))

@app.route('/member/edit/profile/success', methods=['GET'])
def page_member_edit_profile_success():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	return render_template('member/member_edit_profile_success.html', user=user)

##########
## NEWS ##
##########

@app.route('/news', methods=['GET'])
def page_news():
	session['next'] = url_for('page_news')

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	return render_template('news/news-list.html', user=user)

###########################
## ADMINISTRATION ROUTES ##
###########################

@app.route('/admin', methods=['GET'])
def page_admin():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	return render_template('admin/dashboard.html', user=user, active='dashboard')

@app.route('/admin/news', methods=['GET'])
def page_admin_news():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	news_items = NewsItem.query.all()

	return render_template('admin/news.html', user=user, active='news', news_items=news_items)

@app.route('/admin/news/add', methods=['GET', 'POST'])
def page_admin_news_add():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	template_options = {}
	template_options['user'] = user
	template_options['active'] = 'news'
	template_options['staff'] = User.query.filter(User.is_staff==True).filter(User.is_superuser==False).all()
	template_options['superusers'] = User.query.filter(User.is_superuser==True).all()

	if request.method == 'GET':
		return render_template('admin/news-add.html', **template_options)
	else:
		# Request is a POST

		# For each language, if the news item is a draft (which it is, by default) then validation isn't strict. If
		# the item isn't a draft then it will require a proper headline and body.

		# XXX DEBUG: Log the form variables
		result = ''
		for var in request.form:
			result = "\n".join([result, "Param %s = %s" % (var, request.form[var]) ])
		app.logger.info(result)

		# Extract form content

		# YYY Security risk	Not validating the author_id to check that it is one of the presented values, or even that
		# 					the user actually exists. This risk is mitigated by the fact that POSTing to this URL requires
		#					authentication.

		model_vars = {}
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['headline_%s' % lang] = request.form['%s[headline]' % lang]
			model_vars['subhead_%s' % lang] = request.form['%s[subhead]' % lang]
			model_vars['body_%s' % lang] = request.form['%s[body]' % lang]
			model_vars['is_draft_%s' % lang] = request.form['%s[is_draft]' % lang]

		model_vars['author_id'] = request.form['author_id']
		model_vars['date_published'] = request.form['date_published']
		model_vars['is_feature'] = request.form['is_feature']
		model_vars['is_hidden'] = request.form['is_hidden']
		model_vars['allows_comments'] = request.form['allows_comments']

		# XXX Process set the image, if there is one

		# Create the news item
		news_item = NewsItem(**model_vars)
		db.session.add(news_item)
		db.session.commit()

		return url_for('page_admin_news')

@app.route('/admin/news/add/feature_image', methods=['POST'])
def ajax_admin_news_add_feature_image():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	json_results = {}
	json_results['success'] = False
	json_results['image_id'] = 0

	if 'feature_image' in request.files:
		if request.files['feature_image'].filename:

			# Try to import the image. Will be None on failure.
			feature_image = StoredImage.from_file(request.files['feature_image'])

			if feature_image:

				# If it exists in the database, get the stored image. Otherwise, save it.
				tmp_image = StoredImage.from_database_md5(feature_image.md5_hash)
				if tmp_image is None:
					db.session.add(feature_image)
					db.session.commit()
				else:
					feature_image = tmp_image

				json_results['success'] = True
				json_results['image_id'] = feature_image.id

	return jsonify(**json_results)

@app.route('/admin/articles', methods=['GET'])
def page_admin_articles():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	return render_template('admin/articles.html', user=user, active='articles')

@app.route('/admin/lounges', methods=['GET'])
def page_admin_lounges():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	return render_template('admin/lounges.html', user=user, active='lounges')

@app.route('/admin/members', methods=['GET'])
def page_admin_members():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	return render_template('admin/members.html', user=user, active='members')

@app.route('/admin/domains', methods=['GET'])
def page_admin_domains():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	return render_template('admin/domains.html', user=user, active='domains')

#################################
## NON-SERVICEABLE PARTS BELOW ##
#################################

if __name__ == '__main__':
	run_server(app)

