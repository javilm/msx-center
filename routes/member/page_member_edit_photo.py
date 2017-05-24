from __main__ import app, db
from flask import abort, request, render_template, redirect, url_for
from models import User, MemberPortrait, ArticleSeries

@app.route('/member/edit/photo', methods=['GET', 'POST'])
def page_member_edit_photo():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	template_options = {}

	if user is None:
		abort(401)

	template_options['user'] = user
	template_options['navbar_series'] = ArticleSeries.list_for_navbar()

	if request.method == 'GET':
	
		template_options['errors'] = None
		
		return render_template('member/member_edit_photo.html', **template_options)
	else:
		# Request method is POST

		# First update the portrait selection
		if request.form['standard_portrait_number'] is not None:
			user.standard_portrait_id = int(request.form['standard_portrait_number'])
		else:
			user.standard_portrait_id = None
		if request.form['member_portrait_number'] is not None:
			user.member_portrait_id = int(request.form['member_portrait_number'])
		else:
			user.member_portrait_id = None

		db.session.add(user)

		# Then process the upload, if there is one
		upload_handled = False
		if 'uploaded_photo' in request.files:
			src_file = request.files['uploaded_photo']
			if src_file.filename:
				portrait = MemberPortrait(src_file)
				if portrait:
					portrait.user_id = user.id
					db.session.add(portrait)
					db.session.commit()
					user.member_portrait_id = portrait.id
					upload_handled = True
				else:
					template_options['errors'] = "The file you uploaded doesn't seem to be a valid image. Please try a different file."
					return render_template('member/member_edit_photo.html', **template_options)
			# else there was no file upload

		# Save the changes in the database
		db.session.commit()

		# Finally, redirect the user back to his profile view (if there were no uploads) or back to the portrait page (if there were)
		if upload_handled:	
			template_options['errors'] = None
			return render_template('member/member_edit_photo.html', **template_options)
		else:
			return redirect(url_for('page_member', member_id=user.id, slug=user.slug))
