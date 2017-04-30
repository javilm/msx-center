from __main__ import app
from utils import redirect_to_next
from flask import session

@app.route('/signout', methods=['GET'])
def page_signout():
	session.pop('user_id', None)
	return redirect_to_next()
