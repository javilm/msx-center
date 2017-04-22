import json
from flask import jsonify, request
from utils import log_form_vars
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	app.logger.info("*** DEBUG: Length of the items' array with getlist is %s" % len(request.form.getlist('items')))

	log_form_vars(request.form)

	for var in request.form.getlist('items'):
		app.logger.info("*** DEBUG: Related news has ExternalLink #%s" % var)

	return jsonify(request.form.getlist('items'))
