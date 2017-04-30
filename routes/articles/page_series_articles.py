from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries, Article

@app.route('/series/<int:series_id>/<string:slug>', methods=['GET'])
def page_series_articles(series_id, slug):
	session['next'] = url_for('page_series_articles', series_id=series_id, slug=slug)

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()

	# Get the details for this series
	tmeplate_options['series'] = ArticleSeries.query.filter_by(id=series_id).first()

	# Get all the articles in this series
	tmeplate_options['articles'] = Article.query.filter_by(series_id=series_id).order_by(Article.date_published).all()

	# XXX Create this template
	return render_template('articles/articles.html', **template_options)