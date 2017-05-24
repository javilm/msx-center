import json
from __main__ import app, db
from flask import url_for, session, render_template, abort, request
from models import User, NewsItem, ArticleSeries, Comment, Vote
from sqlalchemy import desc

@app.route('/news/<int:news_item_id>/<string:slug>', methods=['GET', 'POST'])
def page_news_item(news_item_id, slug):
	session['next'] = url_for('page_news_item', news_item_id=news_item_id, slug=slug)

	# This news item
	news_item = NewsItem.query.filter_by(id=news_item_id).first()
	if news_item is None:
		abort(404)

	user = User.get_signed_in_user()

	if request.method == 'GET':

		# Update the number of views for this news item
		db.session.add(news_item)
		news_item.num_views += 1
		db.session.commit()

		template_options = {}
		template_options['user'] = user
		template_options['news_item'] = news_item
		template_options['navbar_series'] = ArticleSeries.list_for_navbar()

		# Sidebar's most popular news items
		template_options['popular_news_items'] = NewsItem.query.filter_by(is_draft_en=False, is_published=True, is_hidden=False).order_by(desc(NewsItem.num_views)).limit(10)

		# Get the votes this user cast on this article
		if user:
			votes = db.session.query(Vote).filter(Vote.comment_id == Comment.id).filter(Comment.news_item_id == NewsItem.id).all()
			my_votes = {}
			for vote in votes:
				my_votes[vote.comment_id] = vote.score
			template_options['my_votes'] = my_votes
		else:
			template_options['my_votes'] = None

		return render_template('news/news-item.html', **template_options)

	else:

		app.logger.info("News Item: comment submitted")

		status = '401'

		if news_item.allows_comments:
			comment_params = {}
			comment_params['author'] = user
			comment_params['body_en'] = request.form['reply']
			comment = Comment.new_comment(**comment_params)
			if comment:
				news_item.add_comment(comment)
				status = '200'

		return json.dumps({
			'status': status,
			'url': url_for('page_news_item', news_item_id=news_item_id, slug=slug)
		})
