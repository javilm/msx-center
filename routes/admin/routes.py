import os, string, hashlib, random, re, enum, socket, json, copy
import jinja_filters
import lxml.html as LH
import pycountry
import pytz
from datetime import datetime
from flask import Flask, request, g, render_template, flash, session, url_for, redirect, abort, session, send_file, jsonify
from flask_debugtoolbar import DebugToolbarExtension
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

###########################
#  ADMINISTRATION ROUTES ##
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

@app.route('/admin/categories', methods=['GET'])
def page_admin_categories():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	categories = Category.query.all()

	return render_template('admin/categories.html', user=user, active='categories', categories=categories)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
def page_admin_categories_add():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	if request.method == 'GET':
		# Method is GET
		return render_template('admin/categories-add.html', user=user, active='categories')
	else:
		# Method is POST

		model_vars = {}
		model_vars['name_en'] = request.form['field_name_en']
		model_vars['name_ja'] = request.form['field_name_ja']
		model_vars['name_nl'] = request.form['field_name_nl']
		model_vars['name_es'] = request.form['field_name_es']
		model_vars['name_pt'] = request.form['field_name_pt']
		model_vars['name_kr'] = request.form['field_name_kr']

		# Create the category
		category = Category(**model_vars)
		db.session.add(category)
		db.session.commit()

		return redirect(url_for('page_admin_categories'))

@app.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def page_admin_categories_edit(category_id):
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the category from the database
	category = Category.query.filter_by(id=category_id).first()
	if category is None:
		abort(404)

	if request.method == 'GET':
		# Method is GET
		return render_template('admin/categories-edit.html', user=user, active='categories', category=category)
	else:
		# Method is POST
		category.name_en = LH.document_fromstring(request.form['field_name_en']).text_content() if request.form['field_name_en'] else ''
		category.name_ja = LH.document_fromstring(request.form['field_name_ja']).text_content() if request.form['field_name_ja'] else ''
		category.name_nl = LH.document_fromstring(request.form['field_name_nl']).text_content() if request.form['field_name_nl'] else ''
		category.name_es = LH.document_fromstring(request.form['field_name_es']).text_content() if request.form['field_name_es'] else ''
		category.name_pt = LH.document_fromstring(request.form['field_name_pt']).text_content() if request.form['field_name_pt'] else ''
		category.name_kr = LH.document_fromstring(request.form['field_name_kr']).text_content() if request.form['field_name_kr'] else ''

		# Save the changes
		db.session.add(category)
		db.session.commit()

		return redirect(url_for('page_admin_categories'))

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

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'news'
		template_options['staff'] = User.query.filter(User.is_staff==True).filter(User.is_superuser==False).all()
		template_options['superusers'] = User.query.filter(User.is_superuser==True).all()
		template_options['categories'] = Category.query.order_by(Category.id).all()

		return render_template('admin/news-add.html', **template_options)
	else:
		# Request is a POST

		# For each language, if the news item is a draft (which it is, by default) then validation isn't strict. If
		# the item isn't a draft then it will require a proper headline and body.

		# Extract form content

		# XXX Security risk	Not validating the author_id to check that it is one of the presented values, or even that
		# 					the user actually exists. This risk is mitigated by the fact that POSTing to this URL requires
		#					authentication.

		model_vars = {}
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['headline_%s' % lang] = request.form['%s[headline]' % lang]
			model_vars['subhead_%s' % lang] = request.form['%s[subhead]' % lang]
			model_vars['summary_%s' % lang] = request.form['%s[summary]' % lang]
			model_vars['body_%s' % lang] = request.form['%s[body]' % lang]
			model_vars['is_draft_%s' % lang] = request.form['%s[is_draft]' % lang]

		model_vars['author_id'] = request.form['author_id']
		model_vars['category_id'] = request.form['category_id']
		model_vars['header_image_id'] = request.form['header_image_id']
		model_vars['date_published'] = request.form['date_published']
		model_vars['is_feature'] = request.form['is_feature']
		model_vars['is_hidden'] = request.form['is_hidden']
		model_vars['allows_comments'] = request.form['allows_comments']

		# Create the news item
		news_item = NewsItem(**model_vars)
		db.session.add(news_item)
		db.session.commit()

		return jsonify(url=url_for('page_admin_news'))

@app.route('/admin/news/<int:item_id>/edit', methods=['GET', 'POST'])
def page_admin_news_edit(item_id):

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the news item from the database
	item = NewsItem.query.filter_by(id=item_id).first()
	if item is None:
		abort(404)

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'news'
		template_options['staff'] = User.query.filter(User.is_staff==True).filter(User.is_superuser==False).all()
		template_options['superusers'] = User.query.filter(User.is_superuser==True).all()
		template_options['categories'] = Category.query.order_by(Category.id).all()
		template_options['item'] = item

		return render_template('admin/news-edit.html', **template_options)

	else:
		# XXX Security risk	Not validating the author_id to check that it is one of the presented values, or even that
		# 					the user actually exists. This risk is mitigated by the fact that POSTing to this URL requires
		#					authentication.

		# English
		item.headline_en = request.form['headline_en']
		item.subhead_en = request.form['subhead_en']
		item.summary_en = request.form['summary_en']
		item.body_en = request.form['body_en']
		item.is_draft_en = request.form['is_draft_en']

		# Japanese
		item.headline_ja = request.form['headline_ja']
		item.subhead_ja = request.form['subhead_ja']
		item.summary_ja = request.form['summary_ja']
		item.body_ja = request.form['body_ja']
		item.is_draft_ja = request.form['is_draft_ja']

		# Dutch
		item.headline_nl = request.form['headline_nl']
		item.subhead_nl = request.form['subhead_nl']
		item.summary_nl = request.form['summary_nl']
		item.body_nl = request.form['body_nl']
		item.is_draft_nl = request.form['is_draft_nl']

		# Spanish
		item.headline_es = request.form['headline_es']
		item.subhead_es = request.form['subhead_es']
		item.summary_es = request.form['summary_es']
		item.body_es = request.form['body_es']
		item.is_draft_es = request.form['is_draft_es']

		# Portuguese
		item.headline_pt = request.form['headline_pt']
		item.subhead_pt = request.form['subhead_pt']
		item.summary_pt = request.form['summary_pt']
		item.body_pt = request.form['body_pt']
		item.is_draft_pt = request.form['is_draft_pt']

		# Korean
		item.headline_kr = request.form['headline_kr']
		item.subhead_kr = request.form['subhead_kr']
		item.summary_kr = request.form['summary_kr']
		item.body_kr = request.form['body_kr']
		item.is_draft_kr = request.form['is_draft_kr']

		item.author_id = request.form['author_id']
		item.category_id = request.form['category_id']
		item.header_image_id = request.form['header_image_id']
		item.date_published = request.form['date_published']
		item.is_feature = request.form['is_feature']
		item.is_hidden = request.form['is_hidden']
		item.allows_comment = request.form['allows_comments']

		# Update the news item
		db.session.add(item)
		db.session.commit()

		return jsonify(url=url_for('page_admin_news'))

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

	lounges = ConversationLounge.query.order_by(ConversationLounge.priority).all()

	return render_template('admin/lounges.html', user=user, active='lounges', lounges=lounges)

@app.route('/admin/lounges/add', methods=['GET', 'POST'])
def page_admin_lounges_add():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	if request.method == 'GET':
		return render_template('admin/lounges-add.html', user=user, active='lounges')
	else:
		# DEBUG
		log_form_vars(request.form)

		# Method is POST

		# XXX	No validation in the controller, but there's sanitation in the model constructor. At most we'll have 
		#		conversation lounges with empty slugs, names, etc
		color_classes = ['default', 'primary', 'success', 'info', 'warning', 'danger']

		model_vars = {}
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['name_%s' % lang] = request.form['name_%s' % lang]
			model_vars['desc_%s' % lang] = request.form['desc_%s' % lang]

		model_vars['allows_anonymous'] = request.form['allows_anonymous'] if 'allows_anonymous' in request.form else False
		model_vars['allows_nicknames'] = request.form['allows_nicknames'] if 'allows_nicknames' in request.form else False
		model_vars['allows_unverified'] = request.form['allows_unverified'] if 'allows_unverified' in request.form else False
		model_vars['allows_new'] = request.form['allows_new'] if 'allows_new' in request.form else False
		model_vars['allows_bad_reputation'] = request.form['allows_bad_reputation'] if 'allows_bad_reputation' in request.form else False
		model_vars['staff_only'] = request.form['staff_only'] if 'staff_only' in request.form else False
		model_vars['is_visible'] = request.form['is_visible'] if 'is_visible' in request.form else False
		model_vars['is_readonly'] = request.form['is_readonly'] if 'is_readonly' in request.form else False
		model_vars['priority'] = int(request.form['priority'])
		model_vars['color_class'] = color_classes[int(request.form['color_class'])]
		model_vars['slug'] = request.form['slug']

		# Create the lounge
		lounge = ConversationLounge(**model_vars)
		db.session.add(lounge)
		db.session.commit()

		return redirect(url_for('page_admin_lounges'))

@app.route('/admin/lounges/<int:lounge_id>/edit', methods=['GET', 'POST'])
def page_admin_lounges_edit(lounge_id):
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the news item from the database
	lounge = ConversationLounge.query.filter_by(id=lounge_id).first()
	if lounge is None:
		abort(404)

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'lounges'
		template_options['lounge'] = lounge

		return render_template('admin/lounges-edit.html', **template_options)

	else:
		# DEBUG
		log_form_vars(request.form)

		# Method is POST
		# XXX	No validation in the controller, but there's sanitation in the model constructor. At most we'll have 
		#		conversation lounges with empty slugs, names, etc
		color_classes = ['default', 'primary', 'success', 'info', 'warning', 'danger']

		lounge.name_en = LH.document_fromstring(request.form['name_en']).text_content() if request.form['name_en'] else ''
		lounge.desc_en = LH.document_fromstring(request.form['desc_en']).text_content() if request.form['desc_en'] else ''
		lounge.name_ja = LH.document_fromstring(request.form['name_ja']).text_content() if request.form['name_ja'] else ''
		lounge.desc_ja = LH.document_fromstring(request.form['desc_ja']).text_content() if request.form['desc_ja'] else ''
		lounge.name_nl = LH.document_fromstring(request.form['name_nl']).text_content() if request.form['name_nl'] else ''
		lounge.desc_nl = LH.document_fromstring(request.form['desc_nl']).text_content() if request.form['desc_nl'] else ''
		lounge.name_es = LH.document_fromstring(request.form['name_es']).text_content() if request.form['name_es'] else ''
		lounge.desc_es = LH.document_fromstring(request.form['desc_es']).text_content() if request.form['desc_es'] else ''
		lounge.name_pt = LH.document_fromstring(request.form['name_pt']).text_content() if request.form['name_pt'] else ''
		lounge.desc_pt = LH.document_fromstring(request.form['desc_pt']).text_content() if request.form['desc_pt'] else ''
		lounge.name_kr = LH.document_fromstring(request.form['name_kr']).text_content() if request.form['name_kr'] else ''
		lounge.desc_kr = LH.document_fromstring(request.form['desc_kr']).text_content() if request.form['desc_kr'] else ''
		lounge.allows_anonymous = request.form['allows_anonymous'] if 'allows_anonymous' in request.form else False
		lounge.allows_nicknames = request.form['allows_nicknames'] if 'allows_nicknames' in request.form else False
		lounge.allows_unverified = request.form['allows_unverified'] if 'allows_unverified' in request.form else False
		lounge.allows_new = request.form['allows_new'] if 'allows_new' in request.form else False
		lounge.allows_bad_reputation = request.form['allows_bad_reputation'] if 'allows_bad_reputation' in request.form else False
		lounge.staff_only = request.form['staff_only'] if 'staff_only' in request.form else False
		lounge.is_visible = request.form['is_visible'] if 'is_visible' in request.form else False
		lounge.is_readonly = request.form['is_readonly'] if 'is_readonly' in request.form else False
		lounge.priority = int(request.form['priority'])
		lounge.color_class = color_classes[int(request.form['color_class'])]
		lounge.slug = request.form['slug']

		# Save the lounge
		db.session.add(lounge)
		db.session.commit()

		return redirect(url_for('page_admin_lounges'))


@app.route('/admin/members', methods=['GET'])
def page_admin_members():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Get the list of members
	members = User.query.all()

	return render_template('admin/members.html', user=user, members=members, active='members')

@app.route('/admin/members/<int:member_id>/edit', methods=['GET', 'POST'])
def page_admin_members_edit(member_id):
	return "Not implemented yet"

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

