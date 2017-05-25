from __main__ import app
from flask import session, url_for, render_template
from models import User, ArticleSeries

@app.route('/terms', methods=['GET'])
def page_terms():
	session['next'] = url_for('page_terms')

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['active'] = 'abou'
	template_options['navbar_series'] = ArticleSeries.list_for_navbar()

	return render_template('terms.html', **template_options)
