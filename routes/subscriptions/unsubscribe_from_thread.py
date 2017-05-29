import json
from models import User, ConversationThread, EmailSubscription
from __main__ import app

@app.route('/thread/<int:thread_id>/unsubscribe', methods=['GET'])
def unsubscribe_from_thread(thread_id):

	member = User.get_signed_in_user()

	subscribed = 'n/a'

	if member is None:
		status = '401'
	else:
		thread = ConversationThread.query.filter_by(id=thread_id).first()
		if thread is None:
			status = '404'	

	if member and thread:
		EmailSubscription.unsubscribe(member=member, thread=thread)
		status = '200'
		subscribed = 'n'

	return json.dumps({
		'status': status,
		'subscribed': subscribed
	})
