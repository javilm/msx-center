from __main__ import db
from . import StoredImage

class MemberPortrait(db.Model):
	__tablename__ = 'member_portraits'
	
	id = db.Column(db.Integer, primary_key=True)
	original_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	standard_portrait_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	thumbnail_portrait_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	
	def __init__(self, src_file):
	
		# Store the original image
		original = StoredImage.from_file(src_file)
		
		if original:	# Will be None if the original couldn't be imported
			db.session.add(original)
			db.session.commit()
			self.original_id = original.id
		
			# Create standard portrait
			standard_portrait = StoredImage.from_original(original)
			standard_portrait.make_square()
			standard_portrait.fit_within(256, 256)
			
			# Create portrait thumbnail
			thumbnail_portrait = StoredImage.from_original(original)
			thumbnail_portrait.make_square()
			thumbnail_portrait.fit_within(64, 64)

			# Save the new portraits in the database and store the IDs in the instance
			db.session.add(standard_portrait)
			db.session.add(thumbnail_portrait)
			db.session.commit()
			self.standard_portrait_id = standard_portrait.id
			self.thumbnail_portrait_id = thumbnail_portrait.id
			
		else:
			return None
