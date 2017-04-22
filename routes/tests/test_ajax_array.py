import json
from flask import jsonify, request, json
from utils import log_form_vars
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	log_form_vars(request.json)

	for var in request.json.loads('items'):
		app.logger.info("*** DEBUG: Related news has ExternalLink #%s" % var)

	return jsonify(request.json)
