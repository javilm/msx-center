import os, string, hashlib, random, re
from datetime import datetime
from flask import Flask, request, g, render_template, flash, session, url_for, redirect, abort, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from validate_email import validate_email
from lxml import etree
import lxml.html as LH

from server import run_server

# Create and initialize app
app = Flask(__name__)
app.debug = True
app.config.from_object(__name__)
mail = Mail(app)
db = SQLAlchemy(app)

# Load default config and override config from an environment variable
app.config.update(dict(
	SQLALCHEMY_DATABASE_URI='postgresql://devmsx-centercom:zazuKQ9c@192.168.1.104/devmsx-centercom',
	MAIL_SERVER='192.168.1.200',
	DEFAULT_MAIL_SENDER='javi.lavandeira@msx-center.com',
	SECRET_KEY='e620f0121309a360fc596c481efd895da1c19b1e9358e87a',
	SERVER_NAME='dev.msx-center.com'
))
app.config.from_envvar('MSXCENTER_SETTINGS', silent=True)

############
## MODELS ##
############

class User(db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	real_name = db.Column(db.String)
	nickname = db.Column(db.String, unique=True)
	email = db.Column(db.String, unique=True)
	password_hash = db.Column(db.String)
	registration_date = db.Column(db.DateTime)
	last_signin_date = db.Column(db.DateTime)
	is_active = db.Column(db.Boolean)
	is_new = db.Column(db.Boolean)
	is_blocked = db.Column(db.Boolean)
	is_verified = db.Column(db.Boolean)
	is_superuser = db.Column(db.Boolean)
	is_staff = db.Column(db.Boolean)
	reputation = db.Column(db.Integer)

	@classmethod
	def generate_random_password(cls, length=8):
		return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))

	@classmethod
	def is_signed_in(cls):
		return 'user_id' in session

	@classmethod
	def get_signed_in_user(cls):
		if cls.is_signed_in():
			return User.query.filter_by(id=session['user_id']).first()
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

class Image(db.Model):
	"""Stores all images in the site."""
	__tablename__ = 'images'

	id = db.Column(db.Integer, primary_key=True)
	md5_hash = db.Column(db.String(32), unique=True)
	mime_type = db.Column(db.String())
	original_data = db.Column(db.LargeBinary)
	upload_date = db.Column(db.DateTime)

	def __init__(self, datauri):
		"""Extracts the Image data from the data-uri 'data:image/png;base64,iVBORw0KGgo...' and
		creates a new Image object."""
		self.mime_type = datauri.split(':')[1].split(';')[0] 
		self.original_data = datauri.split(',')[1].decode('base64')
		self.upload_date = datetime.utcnow()
		self.md5_hash = hashlib.md5(self.original_data).hexdigest()

	def ext(self):
		return self.mime_type.split('/')[1]

	def save(self, filename):
		fh = open(filename, "wb")
		fh.write(self.original_data)
		fh.close()

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

	def __init__(self, name_en, desc_en, name_ja=None, name_es=None, name_nl=None, name_pt=None, name_kr=None, desc_ja=None, desc_es=None, desc_nl=None, desc_pt=None, desc_kr=None):

		# Lounge name in several languages
		self.name_en = name_en
		self.name_ja = name_ja or name_en
		self.name_es = name_es or name_en
		self.name_nl = name_nl or name_en
		self.name_pt = name_pt or name_en
		self.name_kr = name_kr or name_en

		# Lounge description in several languages
		self.desc_en = desc_en
		self.desc_ja = desc_ja or name_en
		self.desc_es = desc_es or name_en
		self.desc_nl = desc_nl or name_en
		self.desc_pt = desc_pt or name_en
		self.desc_kr = desc_kr or name_en

		# Flags and metadata
		self.allows_anonymous = False
		self.allows_nicknames = False
		self.allows_unverified = False
		self.allows_new = False
		self.allows_bad_reputation = False
		self.staff_only = True
		self.is_visible = True
		self.is_readonlh = False
		self.num_threads = 99
		self.priority = 10
		self.color_class = 'success'
class ConversationThread(db.Model):
	__tablename__ = 'threads'

	id = db.Column(db.Integer, primary_key=True)
	lounge_id = db.Column(db.Integer, db.ForeignKey('lounges.id'))
	lounge = db.relationship('ConversationLounge', backref=db.backref('threads', lazy='dynamic'))
	title_en = db.Column(db.String())
	title_ja = db.Column(db.String())
	title_nl = db.Column(db.String())
	title_es = db.Column(db.String())
	title_pt = db.Column(db.String())
	title_kr = db.Column(db.String())
	is_popular = db.Column(db.Boolean)
	is_trending = db.Column(db.Boolean)
	is_sticky = db.Column(db.Boolean)
	# The three fields below can be pulled from the backref to the lounge
	#allows_anonymous = db.Column(db.Boolean)
	#allows_nicknames = db.Column(db.Boolean)
	#allows_unverified = db.Column(db.Boolean)
	num_views = db.Column(db.Integer)
	num_messages = db.Column(db.Integer)
	first_post_date = db.Column(db.DateTime)
	last_post_date = db.Column(db.DateTime)


#######################
## APPLICATION SETUP ##
#######################
    
# Create test user
@app.before_first_request
def create_database_tables():
	db.create_all()

	# Delete ConversationLounges if there are any
	ConversationLounge.query.delete()

	# Add initial conversation lounges
	l1 = ConversationLounge('General conversation', "This lounge is for general conversation. You're welcome to discuss anything that would be offtopic in the other lounges.")
	l1.priority = 10
	l1.color_class = 'success'
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
	l3.color_class = 'warning'
	l3.allows_anonymous = False
	l3.allows_nicknames = True
	l3.allows_unverified = True
	l3.allows_bad_reputation = False
	l3.allows_new = True
	l3.staff_only = False
	db.session.add(l3)

	l4 = ConversationLounge('Emulation', "Running emulated systems in modern hardware and conversations about the emulators themselves, rather than the systems being emulated.")
	l4.priority = 40
	l4.color_class = 'danger'
	l4.allows_anonymous = False
	l4.allows_nicknames = True
	l4.allows_unverified = True
	l4.allows_bad_reputation = False
	l4.allows_new = True
	l4.staff_only = False
	db.session.add(l4)

	l5 = ConversationLounge('Trading and collecting', "Our marketplace. Buy and sell stuff!")
	l5.priority = 50
	l5.color_class = 'primary'
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
	l7.color_class = 'info'
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

########################
## APPLICATION ROUTES ##
########################

@app.route('/')
def page_main():
	session['next'] = url_for('page_main')

	if User.is_signed_in():
		user = User.get_signed_in_user()
		if user:
			return render_template('index.html', active_item='home', user=user)
		else:
			# Invalid user ID in session. Remove it from the session and ask the user to sign in again
			session.pop('user_id', None)
			flash('You were signed out. Please sign in again.')
			return redirect(url_for('page_signin'))
	else:
		return render_template('index.html', active_item='home', user=None)

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

	lounges = ConversationLounge.query.order_by(ConversationLounge.priority)
	dummy_threads = [
		{
			'title': "How many kidneys are you selling to donate to Kai's games?",
			'has_new_messages': False,
			'num_views': 134,
			'num_messages': 9823,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Oscar Kenneth Albero'
		},
		{
			'title': "Please donate to my MSX-themed cock ring project",
			'has_new_messages': False,
			'num_views': 2,
			'num_messages': 1,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Oscar Kenneth Albero'
		},
		{
			'title': "Donec vitae finibus orci, faucibus sagittis nunc!!!!! ",
			'has_new_messages': True,
			'num_views': 23,
			'num_messages': 4,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Commodo Sodales'
		},
		{
			'title': "VESTIBULUM BIBENDUM DUI NEC ODIO ULTRICES!",
			'has_new_messages': False,
			'num_views': 1,
			'num_messages': 1,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Lacus Mattis'
		},
		{
			'title': "Lorem ipsum dolor sit MSX consectetur adipiscing elit?",
			'has_new_messages': False,
			'num_views': 23,
			'num_messages': 3,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Cras Dapibus'
		},
		{
			'title': "How many kidneys are you selling to donate to Kai's games?",
			'has_new_messages': False,
			'num_views': 134,
			'num_messages': 9823,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Oscar Kenneth Albero'
		},
		{
			'title': "Please donate to my MSX-themed cock ring project",
			'has_new_messages': False,
			'num_views': 2,
			'num_messages': 1,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Oscar Kenneth Albero'
		},
		{
			'title': "Donec vitae finibus orci, faucibus sagittis nunc!!!!! ",
			'has_new_messages': True,
			'num_views': 23,
			'num_messages': 4,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Commodo Sodales'
		},
		{
			'title': "VESTIBULUM BIBENDUM DUI NEC ODIO ULTRICES!",
			'has_new_messages': False,
			'num_views': 1,
			'num_messages': 1,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Lacus Mattis'
		},
		{
			'title': "Lorem ipsum dolor sit MSX consectetur adipiscing elit?",
			'has_new_messages': False,
			'num_views': 23,
			'num_messages': 3,
			'last_post_date': datetime.utcnow(),
			'last_post_username': 'Cras Dapibus'
		}

	]
	session['next'] = url_for('page_lounges_list')
	return render_template('lounges/lounges-list.html', lounges=lounges, threads=dummy_threads, signed_in=signed_in, user=user)

@app.route('/lounge/<int:lounge_id>/new', methods=['GET', 'POST'])
def page_lounge_post(lounge_id):
	session['next'] = url_for('page_lounge_post', lounge_id=lounge_id)
	if request.method == 'GET':
		# Accessed the URL using the GET method

		# Get the ConversationLounge details
		lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

		# Return a 404 error if the lounge doesn't exist
		if lounge is None:
			abort(404)

		# Get the signed in User (if there's one), or None
		user = User.get_signed_in_user()


		# Validate the user's permissions (the user may be denied posting based on more than one criteria, but
		# the template will only display the first that matches)
		user_errors = {}
		if user is None:
			user_errors['anonymous'] = True
		elif user.is_blocked:
			user_errors['blocked'] = True
		elif user.is_new and not lounge.allows_new:
			user_errors['new'] = True
		elif not user.is_verified and not lounge.allows_unverified:
			user_errors['unverified'] = True
		elif not user.is_staff and lounge.staff_only:
			user_errors['not_staff'] = True
		elif user.reputation < 0 and not loung.allows_bad_reputation:
			user_errors['bad_reputation'] = True

		template_options = {
			'lounge': lounge,
			'user': user,
			'errors': user_errors
		}

		return render_template('lounges/lounges-startconversation.html', **template_options)
	else:
		# Accessed the URL using the POST method
		return "There is nothing here yet"

#########################################################
## XXX Routes below are tests/development/examples XXX ##
#########################################################

@app.route('/editor', methods=['GET', 'POST'])
def page_editortest():
	if request.method == 'GET':
		return render_template('tests/medium-editor.html')
	elif request.method == 'POST':
		app.logger.info("/medium-editor: Accessed the /medium-editor URL with the %s method" % request.method)

		# Log request.form
		dict = request.form
		app.logger.info("/medium-editor: request.form dictionary: %s" % dict)
		app.logger.info("/medium-editor: The POST arguments dictionary has %s items." % len(dict))
		if len(dict):
			for key in dict.keys():
				app.logger.info("/medium-editor: POST[%s]: %s" % (key, dict[key]))

		# Log request.args
		dict = request.args
		app.logger.info("/medium-editor: request.args dictionary: %s" % dict)
		app.logger.info("/medium-editor: The POST arguments dictionary has %s items." % len(dict))
		if len(dict):
			for key in dict.keys():
				app.logger.info("/medium-editor: POST[%s]: %s" % (key, dict[key]))
		
		return "/medium-editor: You POSTed something to the page"
	else:
		app.logger.info("/medium-editor: Accessed the /medium-editor URL with the unsupported %s method" % request.method)
		return "You accessed this page using the %s method" % request.method
		
@app.route('/upload', methods=['GET', 'POST'])
def page_upload():
	if request.method == 'GET':
		return "/upload: You shouldn't be seeing this"
	else:
		app.logger.info("/upload: Accessed the /upload URL with the %s method" % request.method)

		# Log request.form
		dict = request.form
		app.logger.info("/upload: request.form dictionary: %s" % dict)
		app.logger.info("/upload: The POST arguments dictionary has %s items." % len(dict))
		if len(dict):
			for key in dict.keys():
				app.logger.info("/upload: POST[%s]: %s" % (key, dict[key]))

		root = LH.fromstring(dict['content'])
		for el in root.iter('img'):
			img = Image(el.attrib['src'])
			db.session.add(img)
			db.session.commit()
			img.save('/www/javi_lavandeira/dev.msx-center.com/ftproot/htdocs/static/image%s.%s' % (img.id, img.ext()))
			el.attrib['src'] = 'http://dev.msx-center.com/static/image%s.%s' % (img.id, img.ext())
			app.logger.info("Element: %s" % el)

		app.logger.info("Result: %s" % LH.tostring(root))

		return "/upload: You POSTed something to the page"

#################################
## NON-SERVICEABLE PARTS BELOW ##
#################################

if __name__ == '__main__':
	run_server(app)

