from __main__ import app
from flask import abort, render_template
from models import User, ArticleSeries

@app.route('/member/edit/profile/success', methods=['GET'])
def page_member_edit_profile_success():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	template_options = {}

	if user is None:
		abort(401)

	template_options['user'] = user
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('member/member_edit_profile_success.html', **template_options)
