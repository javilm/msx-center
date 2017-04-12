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

from routes.account import *
from routes.lounges import *

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

