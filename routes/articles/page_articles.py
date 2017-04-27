from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries

@app.route('/articles', methods=['GET'])
def page_articles():
	session['next'] = url_for('page_articles')

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()

	# Get all the article series
	tmeplate_options['series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('articles/articles.html', **template_options)