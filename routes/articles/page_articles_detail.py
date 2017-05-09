import json
from __main__ import app, db
from flask import url_for, render_template, session, request, abort
from models import User, ArticleSeries, Article, Comment

@app.route('/articles/<int:article_id>/<string:slug>', methods=['GET', 'POST'])
def page_articles_detail(article_id, slug):
	session['next'] = url_for('page_articles_detail', article_id=article_id, slug=slug)

	# This article
	article = Article.query.filter_by(id=article_id, is_draft_en=False, is_published=True, is_hidden=False).first()
	if article is None:
		abort(404)

	user = User.get_signed_in_user()

	if request.method == 'GET':

		template_options = {}
		template_options['user'] = user
		template_options['article'] = article
		template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()	# all the series, for the navbar
		
		# the series this article belongs to	
		template_options['series'] = ArticleSeries.query.filter_by(id=article.series_id).first()

		return render_template('articles/article-detail.html', **template_options)

	else:
		app.logger.info("Comment submitted")	

		# The form doesn't have to be updated to support AJAX result feedback because the only way to post here is via a direct
		# forged request.

		if article.allows_comments:
			if user is not None:			# Check that the user is logged in...
				if not user.is_blocked:		# ...and that the user is not blocked.

					comment_params = {}
					comment_params['author'] = user
					comment_params['body_en'] = request.form['reply']
					comment = Comment(**comment_params)

					if comment is not None:
						article.comments.append(comment)
						db.session.add(article)
						db.session.add(comment)
						db.session.commit()

		return json.dumps({
			'status': 200,
			'url': url_for('page_articles_detail', article_id=article_id, slug=slug)
		})
