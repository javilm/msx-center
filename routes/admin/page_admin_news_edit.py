import json
from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import Category, NewsItem, User, ExternalLink

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
		template_options['links'] = ExternalLink.query.order_by(ExternalLink.title).all()
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
		item.slug = request.form['slug']
		item.category_id = request.form['category_id']
		item.header_image_id = request.form['header_image_id']
		item.date_published = request.form['date_published']
		item.is_published = request.form['is_published']
		item.is_archived = request.form['is_archived']
		item.is_feature = request.form['is_feature']
		item.is_hidden = request.form['is_hidden']
		item.allows_comment = request.form['allows_comments']

		# Reprocess the body's HTML code in case new images were added
		item.html_extract_images()

		# Remove all existing related links and add the ones from the form
		for link in item.links:
			item.links.remove(link)
		
		links = list(set(json.loads(request.form['links']))) # list(set()) removes the duplicates
		if len(links):
			for link_id in links:
				link = ExternalLink.query.get(link_id)
				if link is not None:
					item.links.append(link)


		# Update the news item
		db.session.add(item)
		db.session.commit()

		return jsonify(url=url_for('page_admin_news'))
