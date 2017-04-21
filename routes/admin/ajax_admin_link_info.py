from flask import abort, jsonify
from __main__ import app, db
from models import ExternalLink, User

@app.route('/admin/link/<int:link_id>/info', methods=['GET'])
def ajax_admin_link_info(link_id):

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	json_results = {}

	link = ExternalLink.query.filter_by(id=link_id).first()
	if link is None:
		json_results['result'] = False
	else:
		json_results['result'] = True
		json_results['id'] = link_id
		json_results['url'] = link.url
		json_results['title'] = link.title

	return jsonify(**json_results)
