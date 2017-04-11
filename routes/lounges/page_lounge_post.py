import json
from __main__ import app
from flask import url_for, request, abort, render_template, session
from models import User, ConversationLounge, ConversationThread, ConversationMessage

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

		# Validate the user's permissions (the user may be denied posting based on more than one criteria, but
		# the template will only display the first that matches)
		user_errors = ConversationLounge.get_permission_errors(user, lounge)

		template_options = {
			'lounge': lounge,
			'user': user,
			'errors': user_errors
		}

		return render_template('lounges/lounges-startconversation.html', **template_options)
	else:
		# Accessed the URL using the POST method, usually via AJAX

		# Get all the request parameters in an ImmutableMultiDict
		dict = request.form
		if len(dict):
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
			elif not user.is_verified and not lounge.allows_unverified:
				user_errors['unverified'] = True
			elif not user.is_staff and lounge.staff_only:
				user_errors['not_staff'] = True
			elif user.reputation < 0 and not lounge.allows_bad_reputation:
				user_errors['bad_reputation'] = True
			# At this point the user is allowed to post. If the user requests to post as anonymous or using a nickname
			# then check whether the lounge allows it.
			elif dict['post_as'] == '3' and lounge.allows_anonymous:
				post_as = 'ANON'
			elif dict['post_as'] == '2' and lounge.allows_nicknames:
				post_as = 'NICKNAME'
			else:
				post_as = 'REALNAME'

			if not user_errors:
				thread = ConversationThread(title_en=dict['title'])
				lounge.add_thread(thread)
				message = ConversationMessage(user, post_as, dict['message'])
				thread.add_message(message)
				return json.dumps({
					'status': 200,
					'url': url_for('page_thread', thread_id=thread.id, slug=thread.slug)
				})
			else:
				return json.dumps(user_errors, sort_keys=True, indent=4)
		else:
			# This is an error, nothing was submitted. Often the case when bots attack the site.
			return "The input dictionary was empty"
