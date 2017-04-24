from flask import abort, redirect, render_template, request, url_for
import lxml.html as LH
from __main__ import app, db
from models import ArticleSeries, User

@app.route('/admin/series/<int:series_id>/edit', methods=['GET', 'POST'])
def page_admin_series_edit(series_id):
	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if user is None:
		abort(401)
	else:
		if not user.is_staff and not user.is_superuser:
			abort(401)

	# Try and retrieve the series from the database
	series = ArticleSeries.query.filter_by(id=series_id).first()
	if series is None:
		abort(404)

	if request.method == 'GET':
		return render_template('admin/series-edit.html', user=user, active='series', series=series)
	else:
		series.title_en = request.form['title_en']
		series.title_ja = request.form['title_ja']
		series.title_nl = request.form['title_nl']
		series.title_es = request.form['title_es']
		series.title_pt = request.form['title_pt']
		series.title_kr = request.form['title_kr']
		series.desc_en = request.form['desc_en']
		series.desc_ja = request.form['desc_ja']
		series.desc_nl = request.form['desc_nl']
		series.desc_es = request.form['desc_es']
		series.desc_pt = request.form['desc_pt']
		series.desc_kr = request.form['desc_kr']
		series.is_hidden = request.form['is_hidden']
		series.is_numbered = request.form['is_numbered']
		series.slug = request.form['slug']
		series.category_id = request.form['category_id']

		db.session.add(series)
		db.session.commit()

		return redirect(url_for('page_admin_series'))

