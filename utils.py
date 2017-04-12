import socket
from flask import session, url_for, redirect
from __main__ import app

def redirect_to_next():
	if 'next' in session:
		url = session['next']
	else:
		url = url_for('page_main')
	return redirect(url)

def get_host_by_ip(ip):
	try:
		data = socket.gethostbyaddr(ip)
		host = repr(data[0])
		return host
	except Exception:
		return None

def log_form_vars(form):
	result = 'Submitted form items:\n\n'

	for var in form:
		result += "%s = %s\n" % (var, form[var])
	app.logger.info(result)
