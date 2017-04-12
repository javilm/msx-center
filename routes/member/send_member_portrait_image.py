from io import BytesIO
from __main__ import app
from flask import abort, send_file
from models import MemberPortrait, StoredImage

@app.route('/member/portrait/<int:portrait_id>/<string:size>')
def send_member_portrait_image(portrait_id, size):
	# If "size" isn't either 'standard' or 'small' then return a 404
	if size != 'standard' and size != 'small':
		abort(404)

	portrait = MemberPortrait.query.filter_by(id=portrait_id).first()
	if portrait is not None:
		if size == 'standard':
			image = StoredImage.query.filter_by(id=portrait.standard_portrait_id).first()
		elif size == 'small':
			image = StoredImage.query.filter_by(id=portrait.thumbnail_portrait_id).first()

		byte_io = BytesIO(image.data)
		return send_file(byte_io, mimetype=image.mime_type)

	else:
		abort(404)
