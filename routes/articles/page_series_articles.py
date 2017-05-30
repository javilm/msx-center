from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries, Article
from sqlalchemy import desc

@app.route('/series/<int:series_id>/<string:slug>', methods=['GET'])
def page_series_articles(series_id, slug):
	session['next'] = url_for('page_series_articles', series_id=series_id, slug=slug)

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['active'] = 'articles'
	template_options['navbar_series'] = ArticleSeries.list_for_navbar()

	template_options['series'] = ArticleSeries.query.filter_by(id=series_id).first()

	# Get all the articles in this series
	template_options['articles'] = Article.query.filter_by(series_id=series_id, is_draft_en=False, is_published=True, is_hidden=False).order_by(Article.date_published).all()

	# Sidebar's most popular articles
	template_options['popular_articles'] = Article.query.filter_by(is_draft_en=False, is_published=True, is_hidden=False).order_by(desc(Article.num_views)).limit(10)

	return render_template('articles/articles-series-detail.html', **template_options)
