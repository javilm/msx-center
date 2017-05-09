import json
from __main__ import app, db
from flask import url_for, render_template, request, abort, session
from models import User, ConversationThread, ConversationMessage, ArticleSeries

@app.route('/lounges/thread/<int:thread_id>/<string:slug>', methods=['GET', 'POST'])
def page_thread(thread_id, slug):
	session['next'] = url_for('page_thread', thread_id=thread_id, slug=slug)

	# Get the signed in User (if there's one), or None
	user = User.get_signed_in_user()
	thread = ConversationThread.query.filter_by(id=thread_id).first()

	if thread is None:
		abort(404)

	if request.method == 'GET':
		# Update the number of views for this thread
		db.session.add(thread)
		thread.num_views += 1
		db.session.commit()

		# Check the user's permission to post in the thread
		user_errors = {}
		if user is None:
			if not thread.lounge.allows_anonymous:
				user_errors['anonymous'] = True
		elif user.is_blocked:
			user_errors['blocked'] = True
		elif user.is_new and not thread.lounge.allows_new:
			user_errors['new'] = True
		elif not user.is_verified and not thread.lounge.allows_unverified:
			user_errors['unverified'] = True
		elif not user.is_staff and thread.lounge.staff_only:
			user_errors['not_staff'] = True
		elif user.reputation < 0 and not thread.lounge.allows_bad_reputation:
			user_errors['bad_reputation'] = True

		# Render the template
		template_options = {
			'user': user,
			'thread': thread,
			'lounge': thread.lounge,
			'errors': user_errors,
			'navbar_series': ArticleSeries.query.order_by(ArticleSeries.priority).all()
		}

		return render_template('lounges/lounges-thread.html', **template_options)

	else:
		if len(request.form):
			# Parameters: post_as, message
			# lounge_id comes from the URI
			# Possible errors:
			#	- lounge does not exist
			#	- failed validation (empty message, anon user in non-anon lounge, etc)
			lounge = thread.lounge

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
			elif request.form['post_as'] == '3' and lounge.allows_anonymous:
				post_as = 'ANON'
			elif request.form['post_as'] == '2' and lounge.allows_nicknames:
				post_as = 'NICKNAME'
			else:
				post_as = 'REALNAME'

			if not user_errors:
				message = ConversationMessage(user, post_as, body_en=request.form['message'])
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
