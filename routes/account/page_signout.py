from __main__ import app, redirect_to_next
from flask import session

@app.route('/signout')
def page_signout():
	session.pop('user_id', None)
	return redirect_to_next()
