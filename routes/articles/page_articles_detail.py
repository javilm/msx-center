from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries, Article

@app.route('/articles/<int:article_id_id>/<string:slug>', methods=['GET'])
def page_articles_detail(article_id, slug):
	session['next'] = url_for('page_articles_detail', article_id=article_id, slug=slug)

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()

	# Get the details for this series
	template_options['series'] = ArticleSeries.query.filter_by(id=series_id).first()

	# Get all the articles in this series
	template_options['article'] = Article.query.filter_by(id=article_id).first()

	# XXX Create this template
	return render_template('articles/article-detail.html', **template_options)