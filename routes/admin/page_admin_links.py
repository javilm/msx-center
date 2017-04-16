from flask import abort, render_template
from __main__ import app
from models import ExternalLink, User

@app.route('/admin/links', methods=['GET'])
def page_admin_links():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	links = ExternalLink.query.all()

	return render_template('admin/links.html', user=user, active='links', links=links)
