import json
from __main__ import app, db
from flask import url_for, render_template, session, request, abort
from models import User, ArticleSeries, Article, Comment, Vote
from sqlalchemy import desc

@app.route('/articles/<int:article_id>/<string:slug>', methods=['GET', 'POST'])
def page_articles_detail(article_id, slug):
	session['next'] = url_for('page_articles_detail', article_id=article_id, slug=slug)

	# This article
	article = Article.query.filter_by(id=article_id, is_draft_en=False, is_published=True, is_hidden=False).first()
	if article is None:
		abort(404)

	user = User.get_signed_in_user()

	if request.method == 'GET':

		# Update the number of views for this article
		db.session.add(article)
		article.num_views += 1
		db.session.commit()

		template_options = {}
		template_options['user'] = user
		template_options['article'] = article
		template_options['navbar_series'] = ArticleSeries.list_for_navbar()
		
		# the series this article belongs to	
		template_options['series'] = ArticleSeries.query.filter_by(id=article.series_id).first()

		# Sidebar's most popular articles
		template_options['popular_articles'] = Article.query.filter_by(is_draft_en=False, is_published=True, is_hidden=False).order_by(desc(Article.num_views)).limit(10)

		# Get the votes this user cast on this article
		if user:
			votes = db.session.query(Vote).filter(Vote.comment_id == Comment.id).filter(Comment.article_id == Article.id).filter(Vote.member_id == user.id).all()
			my_votes = {}
			for vote in votes:
				my_votes[vote.comment_id] = vote.score
			template_options['my_votes'] = my_votes
		else:
			template_options['my_votes'] = None

		return render_template('articles/article-detail.html', **template_options)

	else:
		app.logger.info("Comment submitted")	

		# The form doesn't have to be updated to support AJAX result feedback because the only way to post here is via a direct
		# forged request.

		status = '401'
		status_message = 'You are not allowed to post'

		if article.allows_comments:
			if user is not None:			# Check that the user is logged in...
				if not user.is_blocked:		# ...and that the user is not blocked.

					comment_params = {}
					comment_params['author'] = user
					comment_params['body_en'] = request.form['reply']
					comment = Comment.new_comment(**comment_params)
					if comment:
						article.add_comment(comment)
						status = '200'
						status_message = 'OK'
					else:
						status_message = 'Your comment cannot be empty'
				else:
					status_message = 'You cannot post because your account has been blocked'

		return json.dumps({
			'status': status,
			'status_message': status_message,
			'url': url_for('page_articles_detail', article_id=article_id, slug=slug)
		})

