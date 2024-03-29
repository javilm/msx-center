from flask import abort, render_template
from __main__ import app
from models import User

@app.route('/admin/members', methods=['GET'])
def page_admin_members():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)


	template_options = {}
	template_options['user'] = user
	template_options['active'] = 'members'

	# Get the list of members
	template_options['members'] = User.query.order_by('id')

	return render_template('admin/members.html', **template_options)
