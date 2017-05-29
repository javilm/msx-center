from __main__ import app, db

class EmailSubscription(db.Model):
	__tablename__ = 'email_subscriptions'

	id = db.Column(db.Integer, primary_key=True)

	article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=True)
	article = db.relationship("Article", backref="subscriptions")

	news_item_id = db.Column(db.Integer, db.ForeignKey('news_items.id'), nullable=True)
	news_item = db.relationship("NewsItem", backref="subscriptions")

	thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=True)
	thread = db.relationship("ConversationThread", backref="subscriptions")

	member_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	member = db.relationship("User", backref="subscriptions")

	@classmethod
	def subscribe(cls, member=None, article=None, news_item=None, thread=None):

		result = False

		if member:
			if article:
				exists = EmailSubscription.query.filter_by(member_id=member.id, article_id=article.id).first()
				if not exists:
					result = EmailSubscription(member=member, article=article)
			elif news_item:
				exists = EmailSubscription.query.filter_by(member_id=member.id, news_item_id=news_item.id).first()
				if not exists:
					result = EmailSubscription(member=member, news_item=news_item)
			elif thread:
				exists = EmailSubscription.query.filter_by(member_id=member.id, thread_id=thread.id).first()
				if not exists:
					result = EmailSubscription(member=member, thread=thread)

		if result:
			db.session.add(result)
			db.session.commit()

		return result

	@classmethod
	def unsubscribe(cls, member=None, article=None, news_item=None, thread=None):

		subscription = None

		if member:
			if article:
				subscription = EmailSubscription.query.filter_by(member_id=member.id).filter_by(article_id=article.id).first()
			elif news_item:
				subscription = EmailSubscription.query.filter_by(member_id=member.id, news_item_id=news_item.id).first()
			elif thread:
				subscription = EmailSubscription.query.filter_by(member_id=member.id, thread_id=thread.id).first()

		if subscription:
			db.session.delete(subscription)
			db.session.commit()

	def __init__(self, member=None, article=None, news_item=None, thread=None):

		if member:
			self.member = member
			self.member_id = member.id

			if article:
				self.article = article
				self.article_id = article.id
			elif news_item:
				self.news_item = news_item
				self.news_item_id = news_item.id
			elif thread:
				self.thread = thread
				self.thread_id = thread.id


