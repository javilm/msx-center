from flask import abort, render_template
from __main__ import app
from models import User, ConversationLounge

@app.route('/admin/lounges', methods=['GET'])
def page_admin_lounges():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	template_options = {}
	template_options['user'] = user
	template_options['active'] = 'lounges'
	template_options['lounges'] = ConversationLounge.query.order_by(ConversationLounge.priority).all()

	return render_template('admin/lounges.html', **template_options)
