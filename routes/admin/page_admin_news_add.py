import json
from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import Category, NewsItem, User, ExternalLink, StoredImage

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
		template_options['links'] = ExternalLink.query.order_by(ExternalLink.title).all()

		return render_template('admin/news-add.html', **template_options)
	else:
		# Request is a POST

		# For each language, if the news item is a draft (which it is, by default) then validation isn't strict. If
		# the item isn't a draft then it will require a proper headline and body.

		# XXX Security risk	Not validating the author_id to check that it is one of the presented values, or even that
		# 					the user actually exists. This risk is mitigated by the fact that POSTing to this URL requires
		#					authentication.

		model_vars = {}

		model_vars['headline_en'] = request.form['headline_en']
		model_vars['subhead_en'] = request.form['subhead_en']
		model_vars['summary_en'] = request.form['summary_en']
		model_vars['body_en'] = request.form['body_en']
		model_vars['is_draft_en'] = request.form['is_draft_en']

		model_vars['headline_ja'] = request.form['headline_ja']
		model_vars['subhead_ja'] = request.form['subhead_ja']
		model_vars['summary_ja'] = request.form['summary_ja']
		model_vars['body_ja'] = request.form['body_ja']
		model_vars['is_draft_ja'] = request.form['is_draft_ja']

		model_vars['headline_nl'] = request.form['headline_nl']
		model_vars['subhead_nl'] = request.form['subhead_nl']
		model_vars['summary_nl'] = request.form['summary_nl']
		model_vars['body_nl'] = request.form['body_nl']
		model_vars['is_draft_nl'] = request.form['is_draft_nl']

		model_vars['headline_es'] = request.form['headline_es']
		model_vars['subhead_es'] = request.form['subhead_es']
		model_vars['summary_es'] = request.form['summary_es']
		model_vars['body_es'] = request.form['body_es']
		model_vars['is_draft_es'] = request.form['is_draft_es']

		model_vars['headline_pt'] = request.form['headline_pt']
		model_vars['subhead_pt'] = request.form['subhead_pt']
		model_vars['summary_pt'] = request.form['summary_pt']
		model_vars['body_pt'] = request.form['body_pt']
		model_vars['is_draft_pt'] = request.form['is_draft_pt']

		model_vars['headline_kr'] = request.form['headline_kr']
		model_vars['subhead_kr'] = request.form['subhead_kr']
		model_vars['summary_kr'] = request.form['summary_kr']
		model_vars['body_kr'] = request.form['body_kr']
		model_vars['is_draft_kr'] = request.form['is_draft_kr']

		model_vars['author_id'] = request.form['author_id']
		model_vars['slug'] = request.form['slug']
		model_vars['category_id'] = request.form['category_id']
		model_vars['date_published'] = request.form['date_published']
		model_vars['is_published'] = request.form['is_published']
		model_vars['is_archived'] = request.form['is_archived']
		model_vars['is_feature'] = request.form['is_feature']
		model_vars['is_hidden'] = request.form['is_hidden']
		model_vars['allows_comments'] = request.form['allows_comments']
		
		# Create the news item
		news_item = NewsItem(**model_vars)
		feature_image = StoredImage.query.get(request.form['feature_image_id'])
		news_item.add_feature_image(feature_image)
		db.session.add(news_item)
		
		# Add the related links, if there's any
		links = list(set(json.loads(request.form['links']))) # list(set()) removes the duplicates
		if len(links):
			for link_id in links:
				link = ExternalLink.query.get(link_id)
				if link is not None:
					news_item.links.append(link)
		
		db.session.commit()

		return jsonify(url=url_for('page_admin_news'))

