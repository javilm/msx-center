from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import ExternalLink, User

@app.route('/admin/links/add', methods=['GET', 'POST'])
def page_admin_links_add():

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'links'

		return render_template('admin/links-add.html', **template_options)
	else:
		# Request is a POST

		model_vars = {}
		model_vars['desc_en' % lang] = request.form['desc_en']
		model_vars['desc_ja' % lang] = request.form['desc_ja']
		model_vars['desc_nl' % lang] = request.form['desc_nl']
		model_vars['desc_es' % lang] = request.form['desc_es']
		model_vars['desc_pt' % lang] = request.form['desc_pt']
		model_vars['desc_kr' % lang] = request.form['desc_kr']
		model_vars['url'] = request.form['url']
		model_vars['title'] = request.form['title']

		# Create the link
		link = ExternalLink(**model_vars)
		db.session.add(link)
		db.session.commit()

		return jsonify(url=url_for('page_admin_links'))
