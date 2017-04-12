from __main__ import app
from flask import url_for, session, render_template
from models import User, NewsItem

@app.route('/news', methods=['GET'])
def page_news():
	session['next'] = url_for('page_news')

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	# Get the news items
	#items = db.session.query(NewsItem,User).filter(User.id == NewsItem.author_id).all()
	items = NewsItem.query.order_by(NewsItem.date_published.desc()).limit(5)

	return render_template('news/news-list.html', user=user, items=items)
