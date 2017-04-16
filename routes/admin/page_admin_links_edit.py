from flask import abort, jsonify, render_template, request, url_for
from __main__ import app, db
from models import ExternalLink, User

@app.route('/admin/links/<int:links_id>/edit', methods=['GET', 'POST'])
def page_admin_links_edit(link_id):

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the link from the database
	link = ExternalLink.query.filter_by(id=link_id).first()
	if link is None:
		abort(404)

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'news'
		template_options['staff'] = User.query.filter(User.is_staff==True).filter(User.is_superuser==False).all()
		template_options['superusers'] = User.query.filter(User.is_superuser==True).all()
		template_options['categories'] = Category.query.order_by(Category.id).all()
		template_options['link'] = link

		return render_template('admin/links-edit.html', **template_options)

	else:
		link.desc_en = request.form['desc_en']
		link.desc_ja = request.form['desc_ja']
		link.desc_nl = request.form['desc_nl']
		link.desc_es = request.form['desc_es']
		link.desc_pt = request.form['desc_pt']
		link.desc_kr = request.form['desc_kr']
		link.title = request.form['title']
		link.url = request.form['url']

		# Update the news item
		db.session.add(link)
		db.session.commit()

		return jsonify(url=url_for('page_admin_links'))