from __main__ import app
from flask import session, url_for, render_template
from models import User, ArticleSeries

@app.route('/')
def page_main():
	session['next'] = url_for('page_main')

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()

	# List of article series for the navbar
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('frontpage.html', **template_options)
