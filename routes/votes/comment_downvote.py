import json
from __main__ import app
from flask import abort
from models import Comment, Vote, User

@app.route('/comment/<int:comment_id>/downvote', methods=['GET'])
def comment_downvote(comment_id):

	user = User.get_signed_in_user()
	if user is None:
		abort(401)	# Returning 401 because only forged requests will come here

	comment = Comment.query.filter_by(id=comment_id).first()
	if comment is None:
		abort(401)	# Returning 401 because only forged requests will come here

	vote = Vote.downvote_comment(member=user, comment=comment)

	if vote:
		comment.add_vote(vote)

	return json.dumps({
		'comment_id': comment.id,
		'score': comment.score,
		'num_upvotes': comment.num_upvotes,
		'num_downvotes': comment.num_downvotes
	})
