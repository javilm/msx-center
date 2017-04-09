from flask import abort, redirect, render_template, request, url_for
import lxml.html as LH
from . import ConversationLounge, User

@app.route('/admin/lounges/<int:lounge_id>/edit', methods=['GET', 'POST'])
def page_admin_lounges_edit(lounge_id):
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the news item from the database
	lounge = ConversationLounge.query.filter_by(id=lounge_id).first()
	if lounge is None:
		abort(404)

	if request.method == 'GET':
		template_options = {}
		template_options['user'] = user
		template_options['active'] = 'lounges'
		template_options['lounge'] = lounge

		return render_template('admin/lounges-edit.html', **template_options)

	else:
		# Method is POST
		# XXX	No validation in the controller, but there's sanitation in the model constructor. At most we'll have 
		#		conversation lounges with empty slugs, names, etc
		color_classes = ['default', 'primary', 'success', 'info', 'warning', 'danger']

		lounge.name_en = LH.document_fromstring(request.form['name_en']).text_content() if request.form['name_en'] else ''
		lounge.desc_en = LH.document_fromstring(request.form['desc_en']).text_content() if request.form['desc_en'] else ''
		lounge.name_ja = LH.document_fromstring(request.form['name_ja']).text_content() if request.form['name_ja'] else ''
		lounge.desc_ja = LH.document_fromstring(request.form['desc_ja']).text_content() if request.form['desc_ja'] else ''
		lounge.name_nl = LH.document_fromstring(request.form['name_nl']).text_content() if request.form['name_nl'] else ''
		lounge.desc_nl = LH.document_fromstring(request.form['desc_nl']).text_content() if request.form['desc_nl'] else ''
		lounge.name_es = LH.document_fromstring(request.form['name_es']).text_content() if request.form['name_es'] else ''
		lounge.desc_es = LH.document_fromstring(request.form['desc_es']).text_content() if request.form['desc_es'] else ''
		lounge.name_pt = LH.document_fromstring(request.form['name_pt']).text_content() if request.form['name_pt'] else ''
		lounge.desc_pt = LH.document_fromstring(request.form['desc_pt']).text_content() if request.form['desc_pt'] else ''
		lounge.name_kr = LH.document_fromstring(request.form['name_kr']).text_content() if request.form['name_kr'] else ''
		lounge.desc_kr = LH.document_fromstring(request.form['desc_kr']).text_content() if request.form['desc_kr'] else ''
		lounge.allows_anonymous = request.form['allows_anonymous'] if 'allows_anonymous' in request.form else False
		lounge.allows_nicknames = request.form['allows_nicknames'] if 'allows_nicknames' in request.form else False
		lounge.allows_unverified = request.form['allows_unverified'] if 'allows_unverified' in request.form else False
		lounge.allows_new = request.form['allows_new'] if 'allows_new' in request.form else False
		lounge.allows_bad_reputation = request.form['allows_bad_reputation'] if 'allows_bad_reputation' in request.form else False
		lounge.staff_only = request.form['staff_only'] if 'staff_only' in request.form else False
		lounge.is_visible = request.form['is_visible'] if 'is_visible' in request.form else False
		lounge.is_readonly = request.form['is_readonly'] if 'is_readonly' in request.form else False
		lounge.priority = int(request.form['priority'])
		lounge.color_class = color_classes[int(request.form['color_class'])]
		lounge.slug = request.form['slug']

		# Save the lounge
		db.session.add(lounge)
		db.session.commit()

		return redirect(url_for('page_admin_lounges'))
