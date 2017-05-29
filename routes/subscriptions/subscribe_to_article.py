import json
from models import User, Article, EmailSubscription
from __main__ import app

@app.route('/article/<int:article_id>/subscribe', methods=['GET'])
def subscribe_to_article(article_id):

	member = User.get_signed_in_user()

	subscribed = 'n/a'

	if member is None:
		status = '401'
	else:
		article = Article.query.filter_by(id=article_id).first()
		if article is None:
			status = '404'	

	if member and article:
		subscription = EmailSubscription.subscribe(member=member, article=article)
		if subscription:
			status = '200'
			subscribed = 'y' 

	return json.dumps({
		'status': status,
		'subscribed': subscribed
	})
