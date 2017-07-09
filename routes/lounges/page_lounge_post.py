import json
from __main__ import app
from flask import url_for, request, abort, render_template, session
from models import User, ConversationLounge, ConversationThread, ConversationMessage, ArticleSeries

@app.route('/lounge/<int:lounge_id>/new', methods=['GET', 'POST'])
def page_lounge_post(lounge_id):
	session['next'] = url_for('page_lounge_post', lounge_id=lounge_id)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()

	if request.method == 'GET':
		# Accessed the URL using the GET method

		# Get the ConversationLounge details
		lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

		# Return a 404 error if the lounge doesn't exist
		if lounge is None:
			abort(404)

		template_options = {
			'lounge': lounge,
			'user': user,
			'errors': ConversationLounge.get_permission_errors(user, lounge),
			'navbar_series': ArticleSeries.list_for_navbar()
		}

		return render_template('lounges/lounges-startconversation.html', **template_options)
	else:
		# Accessed the URL using the POST method, usually via AJAX

		# Parameters: title, post_as, message
		# lounge_id comes from the URI
		# Possible errors:
		#	- lounge does not exist
		#	- failed validation (empty title, anon user in non-anon lounge, etc)
		#	- empty message
		lounge = ConversationLounge.query.filter_by(id=lounge_id).first()

		# Validate the user's permissions to post
		user_errors = {}

		if user is None:
			# Anonymous user is only allowed to post if the lounge allows anonymous posts, very easy to check
			if lounge.allows_anonymous:
				post_as = 'ANON'
			else:
				user_errors['anonymous'] = True

		# At this point the user is not anonymous, so we have to check the user's status (blocked, rep, etc) and 
		# the lounge's access permissions to see whether he's allowed to post
		elif user.is_blocked:
			user_errors['blocked'] = True
		elif user.is_new and not lounge.allows_new:
			user_errors['new'] = True
#		elif not user.is_verified and not lounge.allows_unverified:
#			user_errors['unverified'] = True
		elif not user.is_staff and lounge.staff_only:
			user_errors['not_staff'] = True
		elif user.reputation < 0 and not lounge.allows_bad_reputation:
			user_errors['bad_reputation'] = True
		# At this point the user is allowed to post. If the user requests to post as anonymous or using a nickname
		# then check whether the lounge allows it.
		elif request.form['post_as'] == '3' and lounge.allows_anonymous:
			post_as = 'ANON'
		elif request.form['post_as'] == '2' and lounge.allows_nicknames:
			post_as = 'NICKNAME'
		else:
			post_as = 'REALNAME'

		status = '401'
		status_message = 'You are not allowed to post'
		url = ''

		if not user_errors:
			thread = ConversationThread.new_thread(title_en=request.form['title'])
			message = ConversationMessage.new_message(post_as, author=user, body_en=request.form['message'])
			if not thread:
				status_message = 'You have to enter a title for the thread'
			elif not message:
				status_message = 'The message cannot be empty'
			else:
				lounge.add_thread(thread)
				thread.add_message(message)
				status = '200'
				status_message = 'OK'
				url = url_for('page_thread', thread_id=thread.id, slug=thread.slug)

		return json.dumps({
			'status': status,
			'status_message': status_message,
			'url': url
		})
