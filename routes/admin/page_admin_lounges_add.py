from flask import abort, redirect, render_template, request, url_for
from __main__ import app, db
from models import ConversationLounge, User

@app.route('/admin/lounges/add', methods=['GET', 'POST'])
def page_admin_lounges_add():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	if request.method == 'GET':
		return render_template('admin/lounges-add.html', user=user, active='lounges')
	else:
		# DEBUG
		log_form_vars(request.form)

		# Method is POST

		# XXX	No validation in the controller, but there's sanitation in the model constructor. At most we'll have 
		#		conversation lounges with empty slugs, names, etc
		color_classes = ['default', 'primary', 'success', 'info', 'warning', 'danger']

		model_vars = {}
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['name_%s' % lang] = request.form['name_%s' % lang]
			model_vars['desc_%s' % lang] = request.form['desc_%s' % lang]

		model_vars['allows_anonymous'] = request.form['allows_anonymous'] if 'allows_anonymous' in request.form else False
		model_vars['allows_nicknames'] = request.form['allows_nicknames'] if 'allows_nicknames' in request.form else False
		model_vars['allows_unverified'] = request.form['allows_unverified'] if 'allows_unverified' in request.form else False
		model_vars['allows_new'] = request.form['allows_new'] if 'allows_new' in request.form else False
		model_vars['allows_bad_reputation'] = request.form['allows_bad_reputation'] if 'allows_bad_reputation' in request.form else False
		model_vars['staff_only'] = request.form['staff_only'] if 'staff_only' in request.form else False
		model_vars['is_visible'] = request.form['is_visible'] if 'is_visible' in request.form else False
		model_vars['is_readonly'] = request.form['is_readonly'] if 'is_readonly' in request.form else False
		model_vars['priority'] = int(request.form['priority'])
		model_vars['color_class'] = color_classes[int(request.form['color_class'])]
		model_vars['slug'] = request.form['slug']

		# Create the lounge
		lounge = ConversationLounge(**model_vars)
		db.session.add(lounge)
		db.session.commit()

		return redirect(url_for('page_admin_lounges'))
