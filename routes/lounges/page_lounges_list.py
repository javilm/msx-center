from __main__ import app
from flask import url_for, render_template, abort, session, redirect, flash
from models import User, ConversationLounge, ConversationThread, ArticleSeries

@app.route('/lounges', methods=['GET'])
def page_lounges_list():
	session['next'] = url_for('page_lounges_list')

	template_options = {}
	template_options['user'] = User.get_signed_in_user()
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()
	template_options['lounges'] = ConversationLounge.query.order_by(ConversationLounge.priority)

	# Get the latest 5 threads for each lounge
	threads = {}
	for lounge in template_options['lounges']:
		threads[lounge.id] = ConversationThread.query.filter(ConversationThread.lounge_id == lounge.id).order_by(ConversationThread.last_post_date).limit(5).all()

	template_options['threads'] = threads

	return render_template('lounges/lounges-list.html', **template_options)