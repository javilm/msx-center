from flask import abort, redirect, render_template, request, url_for
import lxml.html as LH
from __main__ import app, db
from models import Category, User

@app.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def page_admin_categories_edit(category_id):
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the category from the database
	category = Category.query.filter_by(id=category_id).first()
	if category is None:
		abort(404)

	if request.method == 'GET':

		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'categories'
		template_options['category'] = category
		
		return render_template('admin/categories-edit.html', **template_options)
	else:
		# Method is POST
		category.name_en = LH.document_fromstring(request.form['field_name_en']).text_content() if request.form['field_name_en'] else ''
		category.name_ja = LH.document_fromstring(request.form['field_name_ja']).text_content() if request.form['field_name_ja'] else ''
		category.name_nl = LH.document_fromstring(request.form['field_name_nl']).text_content() if request.form['field_name_nl'] else ''
		category.name_es = LH.document_fromstring(request.form['field_name_es']).text_content() if request.form['field_name_es'] else ''
		category.name_pt = LH.document_fromstring(request.form['field_name_pt']).text_content() if request.form['field_name_pt'] else ''
		category.name_kr = LH.document_fromstring(request.form['field_name_kr']).text_content() if request.form['field_name_kr'] else ''

		# Save the changes
		db.session.add(category)
		db.session.commit()

		return redirect(url_for('page_admin_categories'))
