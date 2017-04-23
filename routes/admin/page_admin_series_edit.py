from flask import abort, redirect, render_template, request, url_for
import lxml.html as LH
from __main__ import app, db
from models import ArticleSeries, User

@app.route('/admin/series/<int:series_id>/edit', methods=['GET', 'POST'])
def page_admin_series_edit(series_id):
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

