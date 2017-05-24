import copy, re, socket
from flask import session, url_for, redirect
from __main__ import app, db

def redirect_to_next():
	if 'next' in session:
		url = session['next']
	else:
		url = url_for('page_main')
	return redirect(url)

def get_host_by_ip(ip):
	try:
		data = socket.gethostbyaddr(ip)
		host = repr(data[0])
		return host
	except Exception:
		return None

def log_form_vars(form):
	result = 'Submitted form items:\n\n'

	for var in form:
		result += "%s = %s\n" % (var, form[var])
	app.logger.info(result)

def html_image_extractor(code, image_max_dimension=1200, add_classes=None, lightbox_format_string=None):

	from lxml import etree
	import lxml.html as LH
	from models import StoredImage

	try:

		root = LH.fromstring(code)

		for element in root.iter('img'):

			# Examine the current IMG element to see whether its SRC attribute is an URL (in which case we skip it and 
			# leave it as it is) or a BASE64-encoded inline image (in which case we extract the image, import it into the 
			# database, and replace the SRC attribute with the URL to the route that serves the imported version of the
			# image.

			exp = re.compile('^data:')

			if exp.match(element.attrib['src']):
				# The element contains an image embedded as a data URI. Import it.

				# Make a copy of the original HTML element
				tmp_element = copy.copy(element)

				# Generate an image by decoding the Base64 content of the src attribute
				img = StoredImage.from_datauri(element.attrib['src'])
				if img.width > image_max_dimension:
					img.fit_within(image_max_dimension, image_max_dimension)

				# Check based on the MD5 hash whether the image was already in the database, save it if it wasn't
				tmp_img = StoredImage.query.filter_by(md5_hash=img.md5_hash).first()
				if tmp_img is None:
					db.session.add(img)
					db.session.commit()
				else:
					img = tmp_img

				# Modify the attributes in the copy of the <img...> tag
				tmp_element.attrib['src'] = url_for('send_image', image_id=img.id, dummy_filename='msx-center_image_%s.jpg' % img.id)

				# Add CSS classes to the element, if any
				if add_classes:
					tmp_element.attrib['class'] = ' '.join(add_classes)

				# Create a new <A ...> element that will contain the modified <IMG ...> tag
				new = etree.Element("a", href=tmp_element.attrib['src'])
				if lightbox_format_string:
					new.attrib['data-lightbox'] = lightbox_format_string

				# Add the <img> tag inside the new <a> element
				new.append(tmp_element)

				# Replace the <img ...> tag in the HTML code with the new <a ...><img ...></a>
				element.getparent().replace(element, new)

				del img, tmp_img

		return LH.tostring(root)

	except etree.XMLSyntaxError:
		return None

def format_datetime(datetime):
	return datetime.strftime('%d/%b/%Y %H:%M:%S')

def format_date(datetime):
	return datetime.strftime('%d/%b/%Y')
