from flask import render_template, url_for
from flask_mail import Message
from __main__ import db, mail, app
from models.EmailSubscription import EmailSubscription

def send_notifications(member=None, thread=None, article=None, news_item=None, comment=None):

	message = Message('[MSX Center] Notification of new reply')
	message.sender = 'MSX Center <no-reply@msx-center.com>'

	template_options = {}
	template_options['comment'] = comment		# sometimes will be a Comment instance, sometimes a ConversationMessage

	if member:
		template_options['reply_author_name'] = member.real_name
	else:
		template_options['reply_author_name'] = 'an anonymous user'

	if article:

		template_options['reply_article_url'] = url_for('page_articles_detail', article_id=article.id, slug=article.slug)
		template_options['reply_article_title'] = article.title_en

		message.html = render_template('email/notification_reply_article.html', **template_options)
		message.body = render_template('email/notification_reply_article.txt', **template_options)

		subscribers = EmailSubscription.query.filter_by(article_id=article.id).all()

	elif thread:

		template_options['reply_thread_url'] = url_for('page_thread', thread_id=thread.id, slug=thread.slug)
		template_options['reply_thread_title'] = thread.title_en

		message.html = render_template('email/notification_reply_thread.html', **template_options)
		message.body = render_template('email/notification_reply_thread.txt', **template_options)

		subscribers = EmailSubscription.query.filter_by(thread_id=thread.id).all()

	elif news_item:

		template_options['reply_news_item_url'] = url_for('page_news_item', news_item_id=news_item.id, slug=news_item.slug)
		template_options['reply_news_item_title'] = news_item.headline_en

		message.html = render_template('email/notification_reply_news_item.html', **template_options)
		message.body = render_template('email/notification_reply_news_item.txt', **template_options)

		subscribers = EmailSubscription.query.filter_by(news_item_id=news_item.id).all()

	for subscriber in subscribers:
		if member.id != subscriber.member_id:
			message.recipients = [subscriber.member.email]
			mail.send(message)
