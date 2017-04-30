from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries, Article

@app.route('/series/<int:series_id>/<string:slug>', methods=['GET'])
def page_series_articles(series_id, slug):
	session['next'] = url_for('page_series_articles', series_id=series_id, slug=slug)

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['active'] = 'articles'
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	template_options['series'] = ArticleSeries.query.filter_by(id=series_id).first()

	# Get all the articles in this series
	template_options['articles'] = Article.query.filter_by(series_id=series_id).order_by(Article.date_published).all()

	return render_template('articles/articles-series-detail.html', **template_options)