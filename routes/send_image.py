from io import BytesIO
from __main__ import app, db
from flask import send_file, abort
from models import StoredImage

@app.route('/image/<int:image_id>/<string:dummy_filename>', methods=['GET'])
def send_image(image_id, dummy_filename):
	image = StoredImage.query.filter_by(id=image_id).first()
	if image is not None:
		db.session.add(image)
		image.num_views += 1
		db.session.commit()

		byte_io = BytesIO(image.data)
		return send_file(byte_io, mimetype=image.mime_type)
	else:
		abort(404)
