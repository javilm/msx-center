from flask import abort, redirect, render_template, request, url_for, jsonify
from __main__ import app, db
from models import ArticleSeries, User, Category

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

		template_options = {}
		template_options['categories'] = Category.query.order_by(Category.id).all()
		template_options['user'] = user
		template_options['active'] = 'series'
		return render_template('admin/series-add.html', **template_options)

	else:

		model_vars = {}
		for lang in ['en', 'ja', 'nl', 'es', 'pt', 'kr']:
			model_vars['title_%s' % lang] = request.form['title_%s' % lang]
			model_vars['desc_%s' % lang] = request.form['desc_%s' % lang]
		model_vars['is_hidden'] = request.form['is_hidden']
		model_vars['is_numbered'] = request.form['is_numbered']
		model_vars['slug'] = request.form['slug']
		model_vars['category_id'] = request.form['category_id']

		# Create the series
		series = ArticleSeries(**model_vars)
		db.session.add(series)
		db.session.commit()

		return jsonify(url=url_for('page_admin_series'))
