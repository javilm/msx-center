from __main__ import app
from flask import url_for, render_template, abort, session, redirect, flash
from models import User, ConversationLounge, ConversationThread, ArticleSeries

@app.route('/lounges', methods=['GET'])
def page_lounges_list():
	session['next'] = url_for('page_lounges_list')

	template_options = {}
	template_options['user'] = User.get_signed_in_user()
	template_options['navbar_series'] = ArticleSeries.list_for_navbar()
	template_options['lounges'] = ConversationLounge.query.order_by(ConversationLounge.priority)

	return render_template('lounges/lounges-list.html', **template_options)
