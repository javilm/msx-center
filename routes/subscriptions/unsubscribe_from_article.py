import json
from __main__ import app
from models import User, Article, EmailSubscription

@app.route('/article/<int:article_id>/unsubscribe', methods=['GET'])
def unsubscribe_from_article(article_id):

	member = User.get_signed_in_user()

	subscribed = 'n/a'

	if member is None:
		status = '401'
	else:
		article = Article.query.filter_by(id=article_id).first()
		if article is None:
			status = '404'	

	if member and article:
		EmailSubscription.unsubscribe(member=member, article=article)
		status = '200'
		subscribed = 'n'

	return json.dumps({
		'status': status,
		'subscribed': subscribed
	})
