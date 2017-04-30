from __main__ import app, db
from models import User, ArticleSeries
from flask import request, render_template, redirect, url_for, abort

@app.route('/member/edit/background', methods=['GET', 'POST'])
def page_member_edit_background():
	# No 'next' value in session because anonymous users won't be coming here. Therefore, no sense in redirecting here after signing in.
	
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)

	if request.method == 'GET':

		template_options = {}
		template_options['user'] = user
		template_options['navbar_series'] = ArticleSeries.query.order_by(ArticleSeries.priority).all()

		return render_template('member/member_edit_background.html', **template_options)
	else:
		# Request method is POST
		error_message = None
		background_num = int(request.form['standard_background_number'])
		if background_num < 1 or background_num > 6:
			error_message = "The background you selected isn't available. Please try again."
			return render_template('member/member_edit_background.html', user=user)
		else:
			user.standard_background_filename = 'profile_background_%s.jpg' % background_num
			db.session.add(user)
			db.session.commit()
			return redirect(url_for('page_member', member_id=user.id, slug=user.slug))
