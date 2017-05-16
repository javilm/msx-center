from __main__ import app
from flask import session, url_for, render_template
from models import User, ArticleSeries, ConversationMessage, NewsItem, Article

@app.route('/', methods=['GET'])
def page_main():
	session['next'] = url_for('page_main')

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['active'] = None
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()
	template_options['carousel_items'] = NewsItem.query.order_by('date_published').limit(3).all()
	template_options['featured_items'] = Article.query.order_by('date_published').limit(3).all()
	template_options['recent_news_items'] = NewsItem.query.order_by('date_published').limit(10).all()
	template_options['recent_posts'] = ConversationMessage.query.order_by('date_posted').limit(10).all()

	return render_template('frontpage.html', **template_options)
