from __main__ import app
from flask import url_for, render_template, session
from models import User, ArticleSeries, Article

@app.route('/articles/<int:article_id>/<string:slug>', methods=['GET'])
def page_articles_detail(article_id, slug):
	session['next'] = url_for('page_articles_detail', article_id=article_id, slug=slug)

	template_options = {}
	template_options['user'] = User.get_signed_in_user()

	# This article
	article = Article.query.filter_by(id=article_id).first()
	if article is None:
		abort(404)

	template_options['article'] = article
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()	# all the series, for the navbar
	
	# the series this article belongs to	
	template_options['series'] = ArticleSeries.query.filter_by(id=article.series_id).first()


	# XXX Create this template
	return render_template('articles/article-detail.html', **template_options)