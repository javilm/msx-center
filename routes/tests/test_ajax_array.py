import json
from flask import jsonify, request, json
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	data = request.get_json()
	
	for var in data:
		app.logger.info("*** DEBUG: The JSON data has variable #%s" % var)

	return jsonify(request.json)
