from __main__ import app
from flask import render_template
from models import User, ArticleSeries

@app.errorhandler(401)
@app.errorhandler(403)
def error_401(e):

	template_options = {}

	# Get the signed in User (if there's one), or None
	template_options['user'] = User.get_signed_in_user()
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	return render_template('errors/401.html', **template_options), 401
