from flask import abort, render_template
from __main__ import app
from models import NewsItem, User

@app.route('/admin/news', methods=['GET'])
def page_admin_news():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	news_items = NewsItem.query.all()

	return render_template('admin/news.html', user=user, active='news', news_items=news_items)
