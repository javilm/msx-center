import json
from flask import jsonify, request
from utils import log_form_vars
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	app.logger.info("*** DEBUG: Length of the 'json' array is %s" % len(request.json))

	log_form_vars(request.json)

	for var in request.json['items']:
		app.logger.info("*** DEBUG: Related news has ExternalLink #%s" % var)

	return jsonify(request.json)
