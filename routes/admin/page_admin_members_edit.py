from __main__ import app

@app.route('/admin/members/<int:member_id>/edit', methods=['GET', 'POST'])
def page_admin_members_edit(member_id):
	return "Not implemented yet"
