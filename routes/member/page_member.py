from __main__ import app
from flask import session, url_for, abort, render_template
from models import User, ArticleSeries

@app.route('/member/<int:member_id>', methods=['GET'])
@app.route('/member/<int:member_id>/<string:slug>', methods=['GET'])
def page_member(member_id, slug=None):
	# Note: in the context of this route, the "user" is the logged in user, and the "member" is
	# the user whose profile is being visited. They may or may not be the same.
	session['next'] = url_for('page_member', member_id=member_id, slug=slug)

	template_options = {}
	template_options['user'] = User.get_signed_in_user()
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()
	
	# Get the visited member
	template_options['member'] = User.query.filter_by(id=member_id).first()

	if template_options['member'] is None:
		abort(404)

	return render_template('member/member_view.html', **template_options)
