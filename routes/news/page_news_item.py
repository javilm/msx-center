from __main__ import app
from flask import url_for, session, render_template, abort
from models import User, NewsItem

@app.route('/news/<int:news_item_id>/<string:slug>', methods=['GET'])
def page_news_item(news_item_id, slug):
	session['next'] = url_for('page_news_item', news_item_id=news_item_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	# Get the news item
	news_item = NewsItem.query.filter_by(id=news_item_id).first()

	if news_item is None:
		abort(404)

	return render_template('news/news-item.html', user=user, news_item=news_item)
