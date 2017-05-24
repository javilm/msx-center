from __main__ import app, db
from flask import abort, render_template, redirect, url_for, request
from models import User, ArticleSeries

@app.route('/member/edit/password', methods=['GET', 'POST'])
def page_member_edit_password():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.

	template_options = {}
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	template_options['user'] = user
	template_options['navbar_series'] = ArticleSeries.list_for_navbar()

	if request.method == 'GET':

		template_options['errors'] = None
		return render_template('member/member_edit_password.html', **template_options)

	else:
		# Method is POST, user trying to change the passwordd
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if request.form['new_pass'] != request.form['new_pass_conf']:
			num_validation_errors += 1
			error_messages.append("The passwords you entered don't match")

		# Check that the new password isn't the same as the current password
		if request.form['new_pass'] == request.form['current_pass']:
			num_validation_errors += 1
			error_messages.append("The new password can't be the same as your current password.")

		# Check that the password passes validation
		if not User.valid_password(request.form['new_pass']):
			num_validation_errors += 1
			error_messages.append("The password doesn't meet all the requirements.")

		# Check that the current password is correct
		if not User.valid_credentials(user.email, request.form['current_pass']):
			num_validation_errors += 1
			error_messages.append("The current password that you entered isn't the one on record.")

		template_options['errors'] = error_messages

		if num_validation_errors:
			return render_template('member/member_edit_password.html', **template_options)
		else:
			user.set_password(request.form['new_pass'])
			db.session.add(user)
			db.session.commit()
			# Redirect instead of rendering the template to avoid resubmission of the form data
			return redirect(url_for('page_member_edit_password_success'))
