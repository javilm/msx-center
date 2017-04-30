from flask import abort, render_template
from __main__ import app
from models import ArticleSeries, User

@app.route('/admin/series', methods=['GET'])
def page_admin_series():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	template_options = {}
	template_options['user'] = user
	template_options['active'] = 'series'
	template_options['series'] = ArticleSeries.query.all()

	return render_template('admin/series.html', **template_options)
