from flask import abort, render_template
from __main__ import app
from models import User, Article

@app.route('/admin/articles', methods=['GET'])
def page_admin_articles():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)
			
	articles = Article.query.order_by(Article.id).all()

	return render_template('admin/articles.html', user=user, active='articles', articles=articles)
