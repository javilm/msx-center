from __main__ import app
from flask import url_for, session, render_template
from models import User, NewsItem, ArticleSeries

@app.route('/news', methods=['GET'], defaults={'page': 1})
@app.route('/news/page/<int:page>', methods=['GET'])
def page_news(page):
	session['next'] = url_for('page_news')

	ITEMS_PER_PAGE = 10

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()

	# Get the news items
	template_options['pagination'] = NewsItem.query.filter_by(is_draft_en=False, is_published=True, is_hidden=False).paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=True)
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('news/news-list.html', **template_options)
