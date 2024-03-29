from flask import abort, jsonify, request
from __main__ import app, db
from models import StoredImage, User

# XXX The code for this route is exactly the same as /admin/news/add/feature_image. At some point
# after the launch, modify both admin sections to use the same one.

@app.route('/admin/articles/add/feature_image', methods=['POST'])
def ajax_admin_articles_add_feature_image():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	json_results = {}
	json_results['success'] = False
	json_results['feature_image_id'] = 0

	if 'feature_image' in request.files:
		if request.files['feature_image'].filename:

			# Try to import the image. Will be None on failure.
			feature_image = StoredImage.from_file(request.files['feature_image'])
			feature_image.fit_within(width=2560, height=2560)

			if feature_image:

				# If it exists in the database, get the stored image. Otherwise, save it.
				tmp_image = StoredImage.from_database_md5(feature_image.md5_hash)
				if tmp_image is None:
					db.session.add(feature_image)
					db.session.commit()
				else:
					feature_image = tmp_image

				json_results['success'] = True
				json_results['feature_image_id'] = feature_image.id

	return jsonify(**json_results)
