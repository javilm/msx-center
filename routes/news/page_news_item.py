from __main__ import app
from flask import url_for, session, render_template, abort
from models import User, NewsItem, ArticleSeries

@app.route('/news/<int:news_item_id>/<string:slug>', methods=['GET'])
def page_news_item(news_item_id, slug):
	session['next'] = url_for('page_news_item', news_item_id=news_item_id, slug=slug)

	template_options = {}
	template_options['user'] = User.get_signed_in_user()

	# Get the news item
	template_options['news_item'] = NewsItem.query.filter_by(id=news_item_id).first()

	if template_options['news_item'] is None:
		abort(404)

	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('news/news-item.html', **template_options)
