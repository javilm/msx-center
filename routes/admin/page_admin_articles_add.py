import json
from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import Category, Article, User, ExternalLink, ArticleSeries, StoredImage

# DEBUG
from utils import log_form_vars

@app.route('/admin/articles/add', methods=['GET', 'POST'])
def page_admin_articles_add():

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
		template_options['active'] = 'articles'
		template_options['staff'] = User.query.filter(User.is_staff==True).filter(User.is_superuser==False).all()
		template_options['superusers'] = User.query.filter(User.is_superuser==True).all()
		template_options['categories'] = Category.query.order_by(Category.id).all()
		template_options['series'] = ArticleSeries.query.order_by(ArticleSeries.id).all()
		template_options['links'] = ExternalLink.query.order_by(ExternalLink.title).all()

		return render_template('admin/articles-add.html', **template_options)
	else:
		# XXX Security risk	Not validating the author_id to check that it is one of the presented values, or even that
		# 					the user actually exists. This risk is mitigated by the fact that POSTing to this URL requires
		#					authentication.

		model_vars = {}
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['title_%s' % lang] = request.form['title_%s' % lang]
			model_vars['summary_%s' % lang] = request.form['summary_%s' % lang]
			model_vars['body_%s' % lang] = request.form['body_%s' % lang]
			model_vars['is_draft_%s' % lang] = request.form['is_draft_%s' % lang]

		model_vars['author_id'] = request.form['author_id']
		model_vars['category_id'] = request.form['category_id']
		model_vars['series_id'] = request.form['series_id']
		model_vars['chapter'] = request.form['chapter']
		model_vars['priority'] = request.form['priority']
		model_vars['level'] = request.form['level']
		model_vars['slug'] = request.form['slug']
		model_vars['date_published'] = request.form['date_published']
		model_vars['is_published'] = request.form['is_published']
		model_vars['is_hidden'] = request.form['is_hidden']
		model_vars['is_archived'] = request.form['is_archived']
		model_vars['is_pinned'] = request.form['is_pinned']
		model_vars['allows_comments'] = request.form['allows_comments']
		
		# Create the news item
		article = Article(**model_vars)
		feature_image = StoredImage.query.get(request.form['feature_image_id'])
		article.add_feature_image(feature_image)
		db.session.add(article)
		
		# Add the related links, if there's any
		links = list(set(json.loads(request.form['links']))) # list(set()) removes the duplicates
		if len(links):
			for link_id in links:
				link = ExternalLink.query.get(link_id)
				if link is not None:
					article.links.append(link)
		
		db.session.commit()

		return jsonify(url=url_for('page_admin_articles'))
