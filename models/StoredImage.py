from datetime import datetime
import hashlib
import string
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage

from __main__ import db

class StoredImage(db.Model):
	__tablename__ = 'stored_images'
	
	id = db.Column(db.Integer, primary_key=True)
	md5_hash = db.Column(db.String(32), unique=True)
	mime_type = db.Column(db.String())
	format = db.Column(db.String())
	width = db.Column(db.Integer)
	height = db.Column(db.Integer)
	data = db.Column(db.LargeBinary)
	datetime_created = db.Column(db.DateTime)
	num_views = db.Column(db.Integer)
	original_id = db.Column(db.Integer, db.ForeignKey('stored_images.id'))
	
	def __init__(self, file=None, datauri=None, original=None):
		if file:
			# Create an image from a file or an instance of Werkzeug's FileStorage class
			if file.__class__ == FileStorage:
				self.data = file.stream.read()
			else:
				self.data = file.getvalue()
			
			self.original_id = None
			
		elif datauri:
			# Read the image data from a Base64-encoded stream in the format:
			# 'data:image/png;base64,iVBORw0KGgo...'
			self.data = datauri.split(',')[1].decode('base64')

			self.original_id = None
			
		elif original:
			# Create a new image by duplicating one from the database
			self.data = original.data
			self.original_id = original.id
		
		else:
			return None

		# Check that the data represents a valid image
		try:
			tmp = Image.open(BytesIO(self.data))
		except IOError:
			return None
			
		# The image was opened without errors
		self.format = tmp.format
		self.mime_type = Image.MIME[tmp.format]
		self.width = tmp.width
		self.height = tmp.height
		self.datetime_created = datetime.utcnow()
		self.num_views = 0
		self.update_md5()
		
	@classmethod
	def from_file(cls, file):
		return cls(file=file)
		
	@classmethod
	def from_datauri(cls, datauri):
		return cls(datauri=datauri)
		
	@classmethod
	def from_original(cls, original):
		return cls(original=original)

	@classmethod
	def from_database_md5(cls, md5_hash):
		"""Returns the image in the database with the given MD5 hash, or None if it doesn't exist"""
		return StoredImage.query.filter_by(md5_hash=md5_hash).first()
		
	def make_square(self):
		"""If the image isn't square then crop it and keep only the central square part."""
		
		# Read image in memory
		original = Image.open(BytesIO(self.data))

		# Do nothing if the image is already square
		if self.width == self.height:
			return True
		
		# Crop if not square
		if self.width > self.height:
			box = (
				(self.width - self.height)/2,
				0,
				(self.width + self.height)/2,
				self.height
			)
		elif self.height > self.width:
			box = (
				0,
				(self.height - self.width)/2,
				self.width,
				(self.height + self.width)/2
			)
		square_image = original.crop(box)

		# Update the data and size values
		tmp_stream = BytesIO()
		square_image.save(tmp_stream, string.upper(self.format))
		self.data = tmp_stream.getvalue()
		self.width = square_image.width
		self.height = square_image.height
		self.update_md5()
		
	def	fit_within(self, width=1200, height=1200):
		"""Make the image fit within (width, height). Replaces the original data."""

		# Read image in memory
		original = Image.open(BytesIO(self.data))
		
		# If the image doesn't fit within (witdth, height) then resample it
		if original.size[0] > width or original.size[1] > height:
			original.thumbnail((width, height), resample=Image.LANCZOS)
			
		# Store the resampled data
		resampled_stream = BytesIO()
		original.save(resampled_stream, string.upper(self.format))
		self.data = resampled_stream.getvalue()
		self.width = original.width
		self.height = original.height
		self.update_md5()

	def update_md5(self):
		self.md5_hash = hashlib.md5(self.data).hexdigest()
