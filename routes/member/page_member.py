from __main__ import app
from flask import session, url_for, abort, render_template
from models import User

@app.route('/member/<int:member_id>/<string:slug>')
def page_member(member_id, slug):
	# Note: in the context of this route, the "user" is the logged in user, and the "member" is
	# the user whose profile is being visited. They may or may not be the same.
	session['next'] = url_for('page_member', member_id=member_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	# Get the visited member
	member = User.query.filter_by(id=member_id).first()

	if member is None:
		abort(404)

	return render_template('member/member_view.html', user=user, member=member)
