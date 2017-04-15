from __main__ import app, db
from flask import send_file, abort
from models import ExternalLink

@app.route('/visit_link/<int:link_id>', methods=['GET'])
def visit_link(link_id):
	link = ExternalLink.query.filter_by(id=link_id).first()
	if link is not None:
		db.session.add(link)
		link.num_visits += 1
		db.session.commit()

		return redirect(link.url)
	else:
		abort(404)
