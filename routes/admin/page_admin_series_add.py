from flask import abort, redirect, render_template
from __main__ import app, db
from models import ArticleSeries, User

@app.route('/admin/series/add', methods=['GET', 'POST'])
def page_admin_series_add():
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	if request.method == 'GET':
		# Method is GET
		return render_template('admin/series-add.html', user=user, active='series')
	else:
		# Method is POST

		model_vars = {}
		model_vars['name_en'] = request.form['field_name_en']
		model_vars['name_ja'] = request.form['field_name_ja']
		model_vars['name_nl'] = request.form['field_name_nl']
		model_vars['name_es'] = request.form['field_name_es']
		model_vars['name_pt'] = request.form['field_name_pt']
		model_vars['name_kr'] = request.form['field_name_kr']

		# Create the category
		series = ArticleSeries(**model_vars)
		db.session.add(series)
		db.session.commit()

		return redirect(url_for('page_admin_series'))
