import json
from flask import jsonify, request, json
from utils import log_form_vars
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	log_form_vars(request.form)

	data = json.loads(request.form['data'])
	app.logger.info("Data: %s" % data)


#	if data:
#		for var in data:
#			app.logger.info("*** DEBUG: The JSON data has variable #%s" % var)
#	else:
#		app.logger.info("Couldn't find any JSON data")

	abort(200)