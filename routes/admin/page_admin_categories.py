from flask import abort, render_template
from __main__ import app
from models import Category, User

@app.route('/admin/categories', methods=['GET'])
def page_admin_categories():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	categories = Category.query.all()

	return render_template('admin/categories.html', user=user, active='categories', categories=categories)
