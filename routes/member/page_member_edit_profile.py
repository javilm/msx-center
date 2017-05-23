from __main__ import app, db, country_list, timezone_list
from flask import abort, request, render_template, redirect, url_for
from slugify import slugify
from models import User, ArticleSeries

@app.route('/member/edit/profile', methods=['GET', 'POST'])
def page_member_edit_profile():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	template_options = {}
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	template_options['user'] = user
	template_options['country_list'] = country_list
	template_options['timezone_list'] = timezone_list
	template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

	if request.method == 'GET':
		return render_template('member/member_edit_profile.html', **template_options)
	else:
		# Method is POST, user trying to change the passwordd
		num_validation_errors = 0
		error_messages = []

		# Check that the passwords match
		if not request.form['real_name'] and not request.form['nickname']:
			num_validation_errors += 1
			error_messages.append("You can't leave blank both your real name and your nickname.")

		if num_validation_errors:
			return render_template('member/member_edit_profile.html', user=user, country_list=country_list, timezone_list=timezone_list, errors=error_messages)
		else:
			user.real_name = request.form['real_name']
			user.nickname = request.form['nickname']
			user.birth_date = request.form['birthdate_field']
			if 'is_public_birthdate' in request.form:
				user.is_public_birth_date = True
			else: 
				user.is_public_birth_date = False
			user.about = request.form['about']
			user.set_from_country(request.form['from_country'])
			user.set_in_country(request.form['in_country'])
			user.timezone = request.form['timezone']
			user.preferred_language = request.form['language'].upper()
			user.website = request.form['website']
			user.facebook = request.form['facebook']
			user.linkedin = request.form['linkedin']
			user.twitter = request.form['twitter']
			user.slug = slugify(slugify(request.form['real_name'] if request.form['real_name'] else request.form['nickname']))
			db.session.add(user)
			db.session.commit()
			# Redirect instead of rendering template to avoid double-posting on page reload
			return redirect(url_for('page_member_edit_profile_success'))
