import json
from __main__ import app
from flask import abort
from models import ConversationMessage, Vote, User

@app.route('/message/<int:message_id>/upvote', methods=['GET'])
def message_upvote(message_id):

	user = User.get_signed_in_user()
	if user is None:
		abort(401)	# Returning 401 because only forged requests will come here

	message = ConversationMessage.query.filter_by(id=message_id).first()
	if message is None:
		abort(401)	# Returning 401 because only forged requests will come here

	vote = Vote.upvote_message(member=user, message=message)

	if vote:
		message.add_vote(vote)
		if message.post_as != message.PostAsType.ANON:
			message.author.update_reputation()  # update the author's reputation
		result = '200'
	else:
		result = '401'

	return json.dumps({
		'result': result,
		'message_id': message.id,
		'score': message.score,
		'num_upvotes': message.num_upvotes,
		'num_downvotes': message.num_downvotes
	})
