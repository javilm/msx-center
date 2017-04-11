from __main__ import app
from flask import url_for, render_template, abort, session, redirect, flash
from models import User, ConversationLounge, ConversationThread

@app.route('/lounges', methods=['GET'])
def page_lounges_list():
	session['next'] = url_for('page_lounges_list')
	user = None
	signed_in = False
	if User.is_signed_in():
		user = User.get_signed_in_user()
		if user is None:
			# Invalid user ID in session. Remove it from the session and ask the user to sign in again
			session.pop('user_id', None)
			flash('You were signed out. Please sign in again.')
			return redirect(url_for('page_signin'))
		else:
			signed_in = True

	# Get all the conversation lounges
	lounges = ConversationLounge.query.order_by(ConversationLounge.priority)

	# Get the latest 5 threads for each lounge
	threads = {}
	for lounge in lounges:
		threads[lounge.id] = ConversationThread.query.filter(ConversationThread.lounge_id == lounge.id).order_by(ConversationThread.last_post_date).limit(5).all()

	return render_template('lounges/lounges-list.html', lounges=lounges, threads=threads, signed_in=signed_in, user=user)