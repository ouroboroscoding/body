# coding=utf8
"""REST

Extends Service to allow for launching as an http accesible rest
service
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-17"

# Python imports
import re
import sys
import traceback

# PIP imports
import bottle
import jsonb
import memory

# Local imports
import errors, response, service

__action_to_method = {
	'create': 'POST',
	'delete': 'DELETE',
	'read':   'GET',
	'update': 'PUT'
}
"""Maps HTTP methods to service actions"""

__content_type = re.compile(r'^application\/json; charset=utf-?8$')
"""Valid Content-Type"""

__noun_regex = re.compile(r'([a-z]+(?:_[a-z]+)*)_(create|delete|read|update)')
"""Regular Expression to match to valid service noun method"""

class __Route(object):
	"""Route

	A private callable class used to store rest routes accessed by bottle
	"""

	__key_to_errors = {
		'data': errors.SERVICE_NO_DATA,
		'session': errors.SERVICE_NO_SESSION
	}
	"""Maps key error variables to their response error code"""

	__on_error = None
	"""On Error

	Function called when a service request raises an exception
	"""

	__service = ''
	"""The service's name"""

	@classmethod
	def on_error(cls, callback: callable):
		"""On Error

		Sets the global error handling function

		Arguments:
			callback (callable): The function to call with the error details

		Returns:
			None
		"""
		cls.__on_error = callback

	@classmethod
	def service(cls, s: str):
		"""Service

		Sets the name of the service associated with all routes

		Arguments:
			s (str): The name of the service

		Returns:
			None
		"""
		cls.__service = s

	def __init__(self, callback: callable, cors: re.Pattern = None):
		"""Constructor

		Initialises an instance of the route

		Arguments:
			callback (callable): The function to pass details to when this route
									is triggered
			cors (re.Pattern): Optional, CORS values

		Returns:
			None
		"""
		self.__callback = callback
		self.__cors = cors

	def __call__(self):
		"""Call (__call__)

		Python magic method that allows the instance to be called

		Returns:
			str
		"""

		# If CORS is enabled and the origin matches
		if self.__cors and 'origin' in bottle.request.headers and self.__cors.match(bottle.request.headers['origin']):
			bottle.response.headers['Access-Control-Allow-Origin'] = bottle.request.headers['origin']
			bottle.response.headers['Vary'] = 'Origin'

		# If the request is OPTIONS, set the headers and return nothing
		if bottle.request.method == 'OPTIONS':
			bottle.response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT, OPTIONS'
			bottle.response.headers['Access-Control-Max-Age'] = 1728000
			bottle.response.headers['Access-Control-Allow-Headers'] = 'Authorization,DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type'
			bottle.response.headers['Content-Type'] = 'text/plain charset=UTF-8'
			bottle.response.headers['Content-Length'] = 0
			bottle.request.status = 204
			return ''

		# Set the return to JSON
		bottle.response.headers['Content-Type'] = 'application/json; charset=utf-8'

		# Initialise the request details with the environment
		dReq = {
			'environment': bottle.request.environ
		}

		# If we got a Read request and the data is in the GET
		if bottle.request.method == 'GET' and 'd' in bottle.request.query:

			# Convert the GET and store the data
			try:
				dReq['data'] = jsonb.decode(bottle.request.query['d'])
			except Exception as e:
				return str(response.Error((errors.REST_REQUEST_DATA, '%s\n%s' % (bottle.request.query['d'], str(e)))))

		# Else we most likely got the data in the body
		else:

			# Make sure the request send JSON
			try:
				if not __content_type.match(bottle.request.headers['Content-Type'].lower()):
					return str(response.Error(errors.REST_CONTENT_TYPE))
			except KeyError:
				return str(response.Error(errors.REST_CONTENT_TYPE))

			# Store the data, if it's too big we need to read it rather than
			#	use getvalue
			try: sData = bottle.request.body.getvalue()
			except AttributeError as e: sData = bottle.request.body.read()

			# Make sure we have a string, not a set of bytes
			try: sData = sData.decode()
			except (UnicodeDecodeError, AttributeError): pass

			# Convert the data and store it
			try:
				if sData: dReq['data'] = jsonb.decode(sData)
			except Exception as e:
				return str(response.Error(errors.REST_REQUEST_DATA,'%s\n%s' % (sData, str(e))))

		# If the request should have sent a session, or one was sent anyway
		if 'Authorization' in bottle.request.headers:

			# Get the session from the Authorization token
			dReq['session'] = memory.load(bottle.request.headers['Authorization'])

			# If the session is not found
			if not dReq['session']:
				bottle.response.status = 401
				return str(response.Error(errors.REST_AUTHORIZATION, 'Unauthorized'))

			# Else, extend the session
			else:
				dReq['session'].extend()

		# In case the service crashes
		try:

			# Call the appropriate API method based on the HTTP/request method
			self.__callback(dReq)

		# If we got a KeyError
		except KeyError as e:
			if e.args[0] in self.__key_to_errors:
				return str(response.Error(self.__key_to_errors[e.args[0]]))
			raise e

		# If we get absolutely any exception
		except Exception as e:

			# Get the traceback info
			sError = traceback.format_exc()

			# Print the traceback to stderr so we log it
			print(sError, file=sys.stderr)

			# If we have an error handler
			if self.__on_error:

				# Gather all the details, including optional ones
				oDetails = {
					'service': self.__service,
					'method': bottle.request.method,
					'path': bottle.request.path,
					'environment': dReq['environment'],
					'traceback': sError
				}
				for s in ['data', 'session']:
					if s in dReq:
						oDetails[s] = dReq[s]

				# Call the error handler with the details
				self.__on_error(oDetails)

			# Set the response that the request crashed
			oResponse = response.Error(
				errors.SERVICE_CRASHED,
				'%s:%s' % (self.__service, bottle.request.path)
			)

		# If there's an error
		if oResponse.error_exists():

			# If it's an authorization error
			if oResponse.error['code'] == errors.REST_AUTHORIZATION:

				# Set the http status to 401 Unauthorized
				bottle.response.status = 401

				# If the message is missing
				if oResponse.error['msg'] == '':
					oResponse.error['msg'] = 'Unauthorized'

			# Add the service and path to the call
			try: oResponse.error['service'].append([self.service, self.path])
			except KeyError: oResponse.error['service'] = [[self.service, self.path]]

		# Return the Response as a string
		return str(oResponse)

class RESTService(bottle.Bottle):
	"""REST Service

	Used to access a service instance via HTTP/REST

	Extends:
		Bottle
	"""

	def __init__(self, name: str, service: service.Service, cors: str = None, on_errors = None):
		"""Constructor

		Creates a new REST instances

		Arguments:
			name (str): The name of the service
			service (Service): The service to make accessible via REST
			cors (str): A regular expression defining what domains can access
						the service
			on_errors (callable): Optional, a function to call when a service
									request throws an exception

		Raises:
			ValueError

		Returns:
			RestService
		"""

		# If the instance is not a Service
		if not isinstance(service, service.Service):
			raise ValueError('Invalis service passed to %s' %
								sys._getframe().f_code.co_name)

		# Store the service
		self.service = service

		# If cors, compile it
		if cors:
			cors = re.compile(cors)

		# Init the urls to functions
		self.__urls = {
			'DELETE': {},
			'GET': {},
			'POST': {},
			'PUT': {}
		}

		# Set the service name
		__Route.service(name)

		# If we have an error handler
		if on_errors:
			__Route.on_error(on_errors)

		# Go through all the functions found on the service
		for sFunc in dir(self.service):

			# Check the format of the method name
			oMatch = self.__noun_regex.match(sFunc)

			# If it's a match
			if oMatch:

				# Get the method
				sMethod = __action_to_method[oMatch.group(2)]

				# Generate the URL
				sUri = '/' + ('/'.join(oMatch.group(1).split('_')))

				# Register it with bottle
				self.route(
					sUri,
					sMethod,
					__Route(
						getattr(self.service, sFunc),	# The function to call
						cors							# Optional CORS regex
					)
				)

	# run method
	def run(self, server='gunicorn', host='127.0.0.1', port=8080,
			reloader=False, interval=1, quiet=False, plugins=None,
			debug=None, maxfile=20971520, **kargs):
		"""Run

		Overrides Bottle's run to default gunicorn and other fields

		Arguments:
			server (str): Server adapter to use
			host (str): Server address to bind to
			port (int): Server port to bind to
			reloader (bool): Start auto-reloading server?
			interval (int): Auto-reloader interval in seconds
			quiet (bool): Suppress output to stdout and stderr?
			plugins (list): List of plugins to the server
			debug (bool): Debug mode
			maxfile (int): Maximum size of requests

		Returns:
			None
		"""

		# Set the max file size
		bottle.BaseRequest.MEMFILE_MAX = maxfile

		# Call bottle run
		bottle.run(
			app=self, server=server, host=host, port=port, reloader=reloader,
			interval=interval, quiet=quiet, plugins=plugins, debug=debug,
			**kargs
		)