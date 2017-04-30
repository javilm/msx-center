from __main__ import app
from flask import url_for, render_template, abort
from models import User, ConversationLounge, ArticleSeries

@app.route('/lounges/<int:lounge_id>/<string:slug>/list', methods=['GET'])
def page_lounge(lounge_id, slug):
	session['next'] = url_for('page_lounge', lounge_id=lounge_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	# Get the ConversationLounge details
	lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

	# Return a 404 error if the lounge doesn't exist
	if lounge is None:
		abort(404)
	
	# Render the template
	template_options = {
		'user': user,
		'lounge': lounge,
		'series': ArticleSeries.query.order_by(ArticleSeries.priority).all()

	}

	return render_template('lounges/lounge-thread-list.html', **template_options)
