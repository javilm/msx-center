from __main__ import app, db, redirect_to_next
from flask import request, session, render_template, redirect, url_for
from models import User, VerificationKey

@app.route('/verifypasswordreset', methods=['GET', 'POST'])
def page_verifypasswordreset():
	
	# If the user is already signed in but comes here anyway, redirect to the front page
	if User.is_signed_in():
		return redirect_to_next()

	if request.method == 'GET':
		if 'key' in request.args:

			key = VerificationKey.query.filter_by(key=request.args['key']).first()

			if key is not None:
				# GET, with a valid activation key
				session['key_id'] = key.id
				user = User.query.filter_by(id=key.user_id).first()
				return render_template('resetpassword-setpassword.html', email=user.email)
			else:
				# GET, 'key' argument is in the URL, but not in the database
				return render_template('resetpassword-getemail.html', invalid_key=True, key=request.args['key'])
		else:
			# GET, but no 'key' argument in the URL
			return render_template('resetpassword-getemail.html')
	else:
		# request.method == 'POST'

		# First confirm that there's a session variable with the key (in case the user POSTs here directly)
		if 'key_id' not in session:
			# No 'key_id' in the session. The user POSTed directly to this form
			return render_template('resetpassword-getemail.html')
		else:
			key = VerificationKey.query.filter_by(id=session['key_id']).first()
			if key is None:
				# There is an invalid key_id in the session, remove it and ask for another
				session.pop('key_id', None)
				return render_template('resetpassword-getemail.html')

		# At this point 'key' contains a valid verification key

		# Validate the password (don't rely on the Javascript validation on the form,
		# because that's only client-side and can be disabled by the user)
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if request.form['password'] != request.form['passwordconfirm']:
			num_validation_errors += 1
			error_messages.append("The passwords you entered don't match")

		# Check that the password passes validation
		if not User.valid_password(request.form['password']):
			num_validation_errors += 1
			error_messages.append("The password doesn't meet all the requirements below")

		# If there were validation errors then display the form again
		if num_validation_errors:
			return render_template('resetpassword-setpassword.html', num_errors=num_validation_errors, error_messages=error_messages)
		else:
			#  Get the User from the database
			user = User.query.filter_by(id=key.user_id).first()

			user.set_password(request.form['password'])		# Set the user password
			user.signin()									# Sign in the user
			db.session.delete(key)							# Delete the activation key
			db.session.commit()								# Save changes

			app.logger.info("User %s <%s> changed his password to %s" % (user.real_name, user.email, request.form['password']))
			user.send_password_reset_success_email()

			# Redirect to the main page
			return redirect(url_for('page_main'))
