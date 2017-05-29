import json
from models import User, NewsItem, EmailSubscription
from __main__ import app

@app.route('/news/<int:news_item_id>/subscribe', methods=['GET'])
def subscribe_to_news_item(news_item_id):

	member = User.get_signed_in_user()

	subscribed = 'n/a'

	if member is None:
		status = '401'
	else:
		news_item = NewsItem.query.filter_by(id=news_item_id).first()
		if news_item is None:
			status = '404'	

	if member and news_item:
		subscription = EmailSubscription.subscribe(member=member, news_item=news_item)
		if subscription:
			status = '200'
			subscribed = 'y' 

	return json.dumps({
		'status': status,
		'subscribed': subscribed
	})
