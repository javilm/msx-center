from __main__ import app
from flask import redirect, url_for, render_template

@app.route('/support', methods=['GET'])
def page_support():

	return redirect(url_for('page_lounge', lounge_id=6, slug='msx-center-help-and-support'))
