from __main__ import app
from flask import session, url_for, render_template
from sqlalchemy import desc
from models import User, ArticleSeries, ConversationMessage, NewsItem, Article

@app.route('/', methods=['GET'])
def page_main():
	session['next'] = url_for('page_main')

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['active'] = 'home'
	template_options['navbar_series'] = ArticleSeries.list_for_navbar()
	template_options['carousel_items'] = NewsItem.query.filter_by(is_feature=True, is_draft_en=False, is_published=True, is_hidden=False).order_by(desc('date_published')).limit(3).all()
	template_options['featured_items'] = Article.query.filter(Article.is_published==True).filter(Article.is_draft_en==False).filter(Article.is_hidden==False).order_by('date_published').limit(3).all()
	template_options['recent_news_items'] = NewsItem.query.filter_by(is_draft_en=False, is_published=True, is_hidden=False).order_by(desc('date_published')).limit(10).all()
	template_options['recent_posts'] = ConversationMessage.query.order_by(desc('date_posted')).limit(10).all()

	return render_template('frontpage.html', **template_options)
