import json
from flask import jsonify, request, json, abort
from utils import log_form_vars
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	log_form_vars(request.form)

	arr = json.loads(request.form['items'])

	app.logger.info("Length of the 'items' array: %s" % len(arr))

	for item in arr:
		app.logger.info("Item in 'items': %s" % item)

	return jsonify(result = 'OK')