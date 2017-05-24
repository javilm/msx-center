from __main__ import app
from flask import session, url_for, abort, render_template
from models import User, ArticleSeries, Vote, Comment, ConversationMessage
from collections import OrderedDict

@app.route('/member/<int:member_id>', methods=['GET'])
@app.route('/member/<int:member_id>/<string:slug>', methods=['GET'])
def page_member(member_id, slug=None):
	# Note: in the context of this route, the "user" is the logged in user, and the "member" is
	# the user whose profile is being visited. They may or may not be the same.
	session['next'] = url_for('page_member', member_id=member_id, slug=slug)

	template_options = {}
	template_options['user'] = User.get_signed_in_user()
	
	# Get the visited member
	template_options['member'] = User.query.filter_by(id=member_id).first()

	if template_options['member'] is None:
		abort(404)

	template_options['navbar_series'] = ArticleSeries.list_for_navbar()

	# Create the timeline
	timeline = {}
	comments = Comment.query.filter_by(author_id=member_id).all()
	votes = Vote.query.filter_by(member_id=member_id).all()
	messages = ConversationMessage.query.filter_by(author_id=member_id).all()
	
	for comment in comments:
		object = {}
		object['type'] = 'comment'
		object['article_id'] = comment.article_id
		object['news_item_id'] = comment.news_item_id
		if comment.article_id:
			object['article'] = comment.article
		elif comment.news_item_id:
			object['news_item'] = comment.news_item
		timeline[comment.date_posted] = object

	for vote in votes:
		object = {}
		object['type'] = 'vote'
		object['member_id'] = vote.member_id
		object['comment_id'] = vote.comment_id
		object['message_id'] = vote.message_id
		if vote.comment_id:
			object['comment'] = vote.comment
		else:
			object['message'] = vote.message
		object['score'] = vote.score
		timeline[vote.date_posted] = object

	for message in messages:
		object = {}
		object['type'] = 'message'
		object['id'] = message.id
		object['thread_id'] = message.thread_id
		object['thread'] = message.thread
		timeline[message.date_posted] = object

	template_options['timeline'] = OrderedDict(sorted(timeline.items(), key=lambda t: t[0]))

	return render_template('member/member_view.html', **template_options)
