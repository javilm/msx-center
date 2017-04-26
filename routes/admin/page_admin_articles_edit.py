import json
from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import Category, Article, User, ExternalLink, ArticleSeries

@app.route('/admin/articles/<int:article_id>/edit', methods=['GET', 'POST'])
def page_admin_articles_edit(article_id):

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the article from the database
	article = Article.query.filter_by(id=article_id).first()
	if article is None:
		abort(404)

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'news'
		template_options['staff'] = User.query.filter(User.is_staff==True).filter(User.is_superuser==False).all()
		template_options['superusers'] = User.query.filter(User.is_superuser==True).all()
		template_options['categories'] = Category.query.order_by(Category.id).all()
		template_options['links'] = ExternalLink.query.order_by(ExternalLink.title).all()
		template_options['series'] = ArticleSeries.query.order_by(ArticleSeries.id).all()
		template_options['article'] = article

		return render_template('admin/articles-edit.html', **template_options)

	else:
		# XXX Security risk	Not validating the author_id to check that it is one of the presented values, or even that
		# 					the user actually exists. This risk is mitigated by the fact that POSTing to this URL requires
		#					authentication.

		# English
		article.title_en = request.form['title_en']
		article.summary_en = request.form['summary_en']
		article.body_en = request.form['body_en']
		article.is_draft_en = request.form['is_draft_en']

		# Japanese
		article.title_ja = request.form['title_ja']
		article.summary_ja = request.form['summary_ja']
		article.body_ja = request.form['body_ja']
		article.is_draft_ja = request.form['is_draft_ja']

		# Dutch
		article.title_nl = request.form['title_nl']
		article.summary_nl = request.form['summary_nl']
		article.body_nl = request.form['body_nl']
		article.is_draft_nl = request.form['is_draft_nl']

		# Spanish
		article.title_es = request.form['title_es']
		article.summary_es = request.form['summary_es']
		article.body_es = request.form['body_es']
		article.is_draft_es = request.form['is_draft_es']

		# Portuguese
		article.title_pt = request.form['title_pt']
		article.summary_pt = request.form['summary_pt']
		article.body_pt = request.form['body_pt']
		article.is_draft_pt = request.form['is_draft_pt']

		# Korean
		article.title_kr = request.form['title_kr']
		article.summary_kr = request.form['summary_kr']
		article.body_kr = request.form['body_kr']
		article.is_draft_kr = request.form['is_draft_kr']

		article.author_id = request.form['author_id']
		article.category_id = request.form['category_id']
		article.series_id = request.form['series_id']
		article.chapter = request.form['chapter']
		article.priority = request.form['priority']
		article.level = request.form['level']
		article.header_image_id = request.form['header_image_id']
		article.slug = request.form['slug']
		article.category_id = request.form['category_id']
		article.date_published = request.form['date_published']
		article.is_hidden = request.form['is_hidden']
		article.is_pinned = request.form['is_pinned']
		article.is_published = request.form['is_published']
		article.is_archived = request.form['is_archived']
		article.allows_comment = request.form['allows_comments']

		# Remove all existing related links and add the ones from the form
		for link in article.links:
			article.links.remove(link)
		
		links = list(set(json.loads(request.form['links']))) # list(set()) removes the duplicates
		if len(links):
			for link_id in links:
				link = ExternalLink.query.get(link_id)
				if link is not None:
					article.links.append(link)

		# Update the news item
		db.session.add(article)
		db.session.commit()

		return jsonify(url=url_for('page_admin_articles'))
