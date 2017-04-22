import json
from flask import jsonify, request, json, abort
from utils import log_form_vars
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	log_form_vars(request.form)

	items = json.loads(request.form['items'])
	app.logger.info("Data: %s" % items)

	return jsonify(result = 'OK')