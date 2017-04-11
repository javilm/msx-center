import string, socket, json
import jinja_filters
import lxml.html as LH
import pycountry
import pytz
from flask import Flask, request, g, render_template, flash, session, url_for, redirect, abort, session, send_file, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from geoip import geolite2
from io import BytesIO
from lxml.html.clean import Cleaner
from server import run_server
from slugify import slugify
from validate_email import validate_email

# Create and initialize app
app = Flask(__name__)
app.jinja_env.filters['pretty_date'] = jinja_filters.pretty_date
app.jinja_env.filters['supress_none'] = jinja_filters.supress_none
app.jinja_env.auto_reload = True
app.debug = True
app.config.from_object(__name__)
mail = Mail(app)
html_cleaner = Cleaner(page_structure=True, links=False)

# Load default config and override config from an environment variable
app.config.update(dict(
	SQLALCHEMY_DATABASE_URI='postgresql://devmsx-centercom:zazuKQ9c@192.168.1.104/devmsx-centercom',
	SQLALCHEMY_ECHO=True,
	MAIL_SERVER='192.168.1.200',
	DEFAULT_MAIL_SENDER='javi.lavandeira@msx-center.com',
	SECRET_KEY='e620f0121309a360fc596c481efd895da1c19b1e9358e87a',
	SERVER_NAME='dev.msx-center.com',
	DEBUG_TB_INTERCEPT_REDIRECTS=False,
	MAX_CONTENT_LENGTH=8*1024*1024
))
app.config.from_envvar('MSXCENTER_SETTINGS', silent=True)

db = SQLAlchemy(app)
toolbar = DebugToolbarExtension(app)

# Create ordered lists of countries and timezones
country_list = sorted(pycountry.countries, key = lambda c: c.name)
timezone_list = sorted(pytz.common_timezones)

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

def log_form_vars(form):
	result = 'Submitted form items:\n\n'

	for var in form:
		result += "%s = %s\n" % (var, form[var])
	app.logger.info(result)

#####################
## Imported models ##
#####################

from models import *

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
			user = User(real_name=request.form['signup_realname'], email=submitted_email, request=request)
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

	# Get the news items
	#items = db.session.query(NewsItem,User).filter(User.id == NewsItem.author_id).all()
	items = NewsItem.query.order_by(NewsItem.date_published.desc()).limit(5)

	return render_template('news/news-list.html', user=user, items=items)

###########################
## ADMINISTRATION ROUTES ##
###########################

from routes.admin import *

#################################
## NON-SERVICEABLE PARTS BELOW ##
#################################

if __name__ == '__main__':
	run_server(app)

