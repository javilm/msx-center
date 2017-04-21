from flask import jsonify, request
from __main__ import app

@app.route('/test/ajax/array', methods=['POST'])
def test_ajax_array():

	app.logger.info("*** DEBUG: Length of the 'links'items' array with getlist is %s" % len(request.form.getlist('items')))

	for var in request.form.getlist('items'):
		app.logger.info("*** DEBUG: Related news has ExternalLink #%s" % link)

	return jsonify(request.form.getlist('items'))
