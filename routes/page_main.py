from __main__ import app
from flask import session, url_for, render_template
from models import User

@app.route('/')
def page_main():
	session['next'] = url_for('page_main')

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	return render_template('frontpage.html', user=user)