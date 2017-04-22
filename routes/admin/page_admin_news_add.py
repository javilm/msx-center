import json
from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import Category, NewsItem, User, ExternalLink

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
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['headline_%s' % lang] = request.form['%s[headline]' % lang]
			model_vars['subhead_%s' % lang] = request.form['%s[subhead]' % lang]
			model_vars['summary_%s' % lang] = request.form['%s[summary]' % lang]
			model_vars['body_%s' % lang] = request.form['%s[body]' % lang]
			model_vars['is_draft_%s' % lang] = request.form['%s[is_draft]' % lang]

		model_vars['author_id'] = request.form['author_id']
		model_vars['slug'] = request.form['slug']
		model_vars['category_id'] = request.form['category_id']
		model_vars['header_image_id'] = request.form['header_image_id']
		model_vars['date_published'] = request.form['date_published']
		model_vars['is_feature'] = request.form['is_feature']
		model_vars['is_hidden'] = request.form['is_hidden']
		model_vars['allows_comments'] = request.form['allows_comments']
		
		# Create the news item
		news_item = NewsItem(**model_vars)
		db.session.add(news_item)
		
		# Add the related links, if there's any
		links = json.loads(request.form['links'])
		if len(links):
			for link_id in links:
				link = ExternalLink.query.get(link_id)
				if link is not None:
					news_item.links.append(link)
		
		db.session.commit()

		return jsonify(url=url_for('page_admin_news'))
