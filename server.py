import time, cherrypy
from paste.translogger import TransLogger

#################################
## NON-SERVICEABLE PARTS BELOW ##
#################################

class FotsTransLogger(TransLogger):
	def write_log(self, environ, method, req_uri, start, status, bytes):
		if bytes is None:
			bytes = '-'
		remote_addr = '-'
		if environ.get('HTTP_X_FORWARDED_FOR'):
			remote_addr = environ['HTTP_X_FORWARDED_FOR']
		elif environ.get('REMOTE_ADDR'):
			remote_addr = environ['REMOTE_ADDR']
		d = {
			'REMOTE_ADDR': remote_addr,
			'REMOTE_USER': environ.get('REMOTE_USER') or '-',
			'REQUEST_METHOD': method,
			'REQUEST_URI': req_uri,
			'HTTP_VERSION': environ.get('SERVER_PROTOCOL'),
			'time': time.strftime('%d/%b/%Y:%H:%M:%S', start),
			'status': status.split(None, 1)[0],
			'bytes': bytes,
			'HTTP_REFERER': environ.get('HTTP_REFERER', '-'),
			'HTTP_USER_AGENT': environ.get('HTTP_USER_AGENT', '-'),
		}
		message = self.format % d
		self.logger.log(self.logging_level, message)

def run_server(app):
	# Enable custom Paste access logging
	log_format = (
		'[%(time)s] REQUEST %(REQUEST_METHOD)s %(status)s %(REQUEST_URI)s '
		'(%(REMOTE_ADDR)s) %(bytes)s'
	)
	app_logged = FotsTransLogger(app, format=log_format)

	# Mount the WSGI callable object (app) on the root directory
	cherrypy.tree.graft(app_logged, '/')

	# Set the configuration of the web server
	cherrypy.config.update({
		'engine.autoreload_on': True,
		'log.screen': True,
		'server.socket_port': 8001,
		'server.socket_host': '127.0.0.1'
	})

	# Start the CherryPy WSGI web server
	cherrypy.engine.start()
	cherrypy.engine.block()
