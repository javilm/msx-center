from __main__ import app
from flask import render_template
from models import User, ArticleSeries

@app.errorhandler(500)
def error_500(e):

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('errors/500.html', **template_options), 500
