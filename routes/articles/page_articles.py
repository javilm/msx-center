from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries

@app.route('/articles', methods=['GET'])
def page_articles():
	session['next'] = url_for('page_articles')

	template_options = {}
	template_options['user'] = User.get_signed_in_user()
	template_options['active'] = 'articles'

	# List of article series for the navbar
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	# Get all the article series
	tmeplate_options['series'] = template_options['navbar_series']

	return render_template('articles/articles.html', **template_options)
