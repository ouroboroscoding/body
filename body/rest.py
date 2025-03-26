# coding=utf8
"""REST

Extends Service to allow for launching as an http accesible rest
service
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-17"

# Limit exports
__all__ = [ 'bottle', 'REST' ]

# Ouroboros imports
from jobject import jobject
import jsonb
import memory
from tools import clone

# Python imports
from datetime import datetime
import re
import sys
import traceback
from typing import List, Literal

# Pip imports
import bottle

# Local imports
from . import errors, response, service

class _Route(object):
	"""Route

	A private callable class used to store rest routes accessed by bottle
	"""

	__content_type = re.compile(r'^application\/json; charset=utf-?8$')
	"""Valid Content-Type"""

	__cors = None
	"""CORs regular expression"""

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

	__uris: dict = {}
	"""URIs
	used to keep track of the uris to callbacks for the purposes of __list calls
	"""

	__verbose = True
	"""The verbose mode, set to True to view requests/responses"""

	@classmethod
	def cors(cls, cors):
		"""CORs

		Sets the regular expression used to validate domains making requests

		Arguments:
			pattern (Re.Pattern): A compiled regular expression

		Returns:
			None
		"""
		cls.__cors = cors

	@classmethod
	def on_error(cls, callback: callable):
		"""On Error

		Sets the global error handling function

		Arguments:
			callback (callable): The function to call with the error details

		Returns:
			None
		"""
		cls.__on_error = staticmethod(callback)

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

	@classmethod
	def verbose(cls, b: bool):
		"""Verbose

		Set the verbose mode associated with all routes

		Arguments:
			b (bool): True/False

		Returns:
			None
		"""
		cls.__verbose = b

	def __init__(self,
		callback: callable | Literal[True],
		uri: str | None = None
	):
		"""Constructor

		Initialises an instance of the route

		Arguments:
			callback (callable): The function to pass details to when this \
				route is triggered. Send True to make a __list route

		Returns:
			None
		"""

		# Store the callback
		self.__callback = callback

		# If we got a uri, associated the callback with it globally, this way
		#	we can reference it when getting __list requests
		if uri is not None:
			self.__uris[uri[1:]] = callback

	def __call__(self):
		"""Call (__call__)

		Python magic method that allows the instance to be called

		Returns:
			str
		"""

		# If CORS is enabled and the origin matches
		if self.__cors and \
			'origin' in bottle.request.headers and \
			self.__cors.match(bottle.request.headers['origin']):

			# Add the current origin as acceptable
			bottle.response.headers['Access-Control-Allow-Origin'] = \
				bottle.request.headers['origin']
			bottle.response.headers['Vary'] = 'Origin'

		# If the request is OPTIONS
		if bottle.request.method == 'OPTIONS':

			# If we're in verbose mode, let people know we are handling OPTIONS
			if self.__verbose:
				print('%s: %s OPTIONS %s' % (
					str(datetime.now()),
					self.__service,
					bottle.request.path
				))

			# Set the default headers expected for OPTIONS
			bottle.response.headers['Access-Control-Allow-Methods'] = \
				'DELETE, GET, POST, PUT, OPTIONS'
			bottle.response.headers['Access-Control-Max-Age'] = 1728000
			bottle.response.headers['Access-Control-Allow-Headers'] = \
				'Authorization,DNT,X-CustomHeader,Keep-Alive,User-Agent,' \
				'X-Requested-With,If-Modified-Since,Cache-Control,Content-Type'
			bottle.response.headers['Content-Type'] = 'text/plain charset=UTF-8'
			bottle.response.headers['Content-Length'] = 0
			bottle.request.status = 204
			return ''

		# Set the return to JSON
		bottle.response.headers['Content-Type'] = \
			'application/json; charset=utf-8'

		# Initialise the request details with the bottle request and response
		#	objects, allowing requests direct access to low level data
		oReq = jobject({
			'request': bottle.request,
			'response': bottle.response
		})

		# If we got a Read request and the data is in the GET
		if bottle.request.method == 'GET' and 'd' in bottle.request.query:

			# Convert the GET and store the data
			try:
				oReq.data = jsonb.decode(bottle.request.query['d'])
			except Exception as e:
				return response.Error((errors.REST_REQUEST_DATA, '%s\n%s' % (bottle.request.query['d'], str(e)))).to_json()

		# Else we most likely got the data in the body
		else:

			# Make sure the request send JSON
			try:
				if not self.__content_type.match(bottle.request.headers['Content-Type'].lower()):
					return str(response.Error(errors.REST_CONTENT_TYPE))
			except KeyError:
				return response.Error(errors.REST_CONTENT_TYPE).to_json()

			# Store the data, if it's too big we need to read it rather than
			#	use getvalue
			try:
				sData = bottle.request.body.getvalue()
			except AttributeError as e:
				sData = bottle.request.body.read()

			# Make sure we have a string, not a set of bytes
			try:
				sData = sData.decode()
			except (UnicodeDecodeError, AttributeError):
				pass

			# Convert the data and store it
			try:
				if sData: oReq.data = jsonb.decode(sData)
			except Exception as e:
				return response.Error(errors.REST_REQUEST_DATA,'%s\n%s' % (sData, str(e))).to_json()

		# If the request sent a authorization token
		if 'Authorization' in bottle.request.headers:

			# Get the session from the Authorization token
			oReq.session = memory.load(bottle.request.headers['Authorization'])

			# If the session is not found
			if not oReq.session:
				bottle.response.status = 401
				return response.Error(errors.REST_AUTHORIZATION, 'Unauthorized').to_json()

			# Else, extend the session's ttl
			else:
				oReq.session.extend()

		# In case the service crashes
		try:

			# If we're in verbose mode
			if self.__verbose:
				print('%s REQUEST %s %s %s %s' % (
					str(datetime.now()),
					self.__service,
					bottle.request.method,
					bottle.request.path,
					str('data' in oReq and jsonb.encode(oReq.data, 2) or 'None')
				))

			# If this is a list request
			if self.__callback is True:

				# If the data isn't passed or isn't an array
				if 'data' not in oReq or not isinstance(oReq.data, list):
					oResponse = response.Error(
						errors.REST_REQUEST_DATA,
						'data must be an array'
					)

				# Else, if it's beyond the max
				elif len(oReq.data) > 10:
					oResponse = response.Error(
						errors.REST_LIST_TO_LONG,
						'Can not request more than 10 urls via __list'
					)

				# Else, we have an array of nouns to call and return
				else:

					# Init the response
					lResponse = []

					# Go through each element in the list
					for m in oReq.data:

						# If we got a string
						if isinstance(m, str):
							m = [ m ]

						# Else, if we didn't get a list
						elif not isinstance(m, list):
							oResponse = response.Error(
								errors.REST_REQUEST_DATA, [ m,
									'data must be an array or URI and data, ' \
									'or single string for the URI' ]
							)
							break

						# If the URI doesn't exist
						if m[0] not in self.__uris:
							oResponse = response.Error(
								errors.REST_LIST_INVALID_URI,
								m[0]
							)
							break

						# Clone the __list request data so that the session
						#	or any other data is shared
						oRequest = clone(oReq)

						# If unique data was passed for the child request
						if len(m) == 2:

							# If we didn't get a dict
							if not isinstance(m[1], dict):
								oResponse = response.Error(
									errors.REST_LIST_INVALID_URI,
									[ m[1], 'data must be an object' ]
								)
								break

							# Set the data for this request
							oRequest.data = m[1]

						# No unique data was sent, so we need to delete the
						#	original data from the request
						else:
							try: del oRequest.data
							except AttributeError: pass

						# Call the request and append the data to the
						#	response
						try:
							lResponse.append([
								m[0],
								self.__uris[m[0]](oRequest).to_dict()
							])

						# If we got a KeyError
						except (AttributeError, KeyError) as e:
							if e.args[0] in self.__key_to_errors:
								oResponse = response.Error(
									self.__key_to_errors[e.args[0]]
								)
								break
							else:
								raise

						# If we got a response exception
						except response.ResponseException as e:

							# Set the response using the exceptions first argument
							oResponse = e.args[0]
							break

					# Else, we got through the list
					else:

						# Set the response using the list of individual
						#	responses
						oResponse = response.Response(lResponse)

			# Else, we are making a single URI request
			else:

				# Call the appropriate API method based on the HTTP/request
				#	method
				try:
					oResponse = self.__callback(oReq)

				# If we got a KeyError
				except (AttributeError, KeyError) as e:
					if e.args[0] in self.__key_to_errors:
						oResponse = response.Error(
							self.__key_to_errors[e.args[0]]
						)
					else:
						raise

				# If we got a response exception
				except response.ResponseException as e:

					# Set the response using the exceptions first argument
					oResponse = e.args[0]

		# If we get absolutely any exception
		except Exception as e:

			# Get the traceback info
			sError = traceback.format_exc()

			# Print the traceback to stderr
			print(sError, file=sys.stderr)

			# If we have an error handler
			if self.__on_error:

				# Gather all the details, including optional ones
				oDetails = {
					'service': self.__service,
					'method': bottle.request.method,
					'path': bottle.request.path,
					'environment': bottle.request.environ,
					'traceback': sError
				}
				for s in ['data', 'session']:
					if s in oReq:
						oDetails[s] = oReq[s]

				# Pass the details to the error handler
				self.__on_error(oDetails)

			# Set a response of service/request crashed
			oResponse = response.Error(
				errors.SERVICE_CRASHED,
				'%s:%s' % (self.__service, bottle.request.path)
			)

		# If the response contains an error
		if oResponse.error:

			# If it's an authorization error
			if oResponse.error['code'] == errors.REST_AUTHORIZATION:

				# Set the http status to 401 Unauthorized
				bottle.response.status = 401

				# If the message is missing
				if oResponse.error['msg'] == '':
					oResponse.error['msg'] = 'Unauthorized'

			# Add the service and path to the call
			try:
				oResponse.error['service'].append([
					self.__service, bottle.request.method, bottle.request.path
				])
			except KeyError:
				oResponse.error['service'] = [
					[self.__service, bottle.request.method, bottle.request.path]
				]

		# If we're in verbose mode
		if self.__verbose:
			print('%s RETURNING %s %s %s %s' % (
				str(datetime.now()),
				self.__service,
				bottle.request.method,
				bottle.request.path,
				jsonb.encode(oResponse.to_dict(), 2)
			)
		)

		# Return the Response as a string
		return oResponse.to_json()

class REST(bottle.Bottle):
	"""REST

	Used to access a service instance via HTTP/REST

	Extends:
		Bottle
	"""

	__action_to_method = {
		'create': 'POST',
		'delete': 'DELETE',
		'read':   'GET',
		'update': 'PUT'
	}
	"""Maps HTTP methods to service actions"""

	__noun_regex = re.compile(
		r'([a-z]+(?:_[a-z]+)*)_(create|delete|read|update)'
	)
	"""Regular Expression to match to valid service noun method"""

	def __init__(self,
		name: str,
		instance: service.Service,
		cors: List[str] = None,
		lists = True,
		on_errors: callable = None,
		verbose: bool = False
	):
		"""Constructor

		Creates a new REST instance

		Arguments:
			name (str): The name of the service
			instance (Service): The service to make accessible via REST
			cors (str[]): A list of allowed domains for CORS policy
			lists (bool | dict): True to add a __list call to the default
				service, else a dictionay of uris to services
			on_errors (callable): Optional, a function to call when a service \
				request throws an exception

		Raises:
			ValueError

		Returns:
			RestService
		"""

		# Call the parent constructor first so the object is setup
		super(REST, self).__init__()

		# If the instance is not a Service
		if not isinstance(instance, service.Service):
			raise ValueError('Invalid service passed to %s' %
								sys._getframe().f_code.co_name)

		# Store the service
		self.instance = instance

		# If cors, compile it
		if cors:

			# If it's not a list
			if not isinstance(cors, list):
				raise RuntimeError('REST.cors must be a list')

			# If we only have one
			if len(cors) == 1:
				cors = cors[0].replace('.', '\\.')
			else:
				cors = '(?:%s)' % '|'.join([
					s.replace('.', '\\.')
					for s in cors
				])
			cors = re.compile('https?://(.*\\.)?%s' % cors)

			# Set it
			_Route.cors(cors)

		# Set the service name
		_Route.service(name)

		# If we have an error handler
		if on_errors:
			_Route.on_error(on_errors)

		# Set the verbose mode
		_Route.verbose(verbose)

		# Go through all the functions found on the service
		for sFunc in dir(self.instance):

			# Check the format of the method name
			oMatch = self.__noun_regex.match(sFunc)

			# If it's a match
			if oMatch:

				# Get the method
				sMethod = self.__action_to_method[oMatch.group(2)]

				# Generate the URL
				sUri = '/' + ('/'.join(oMatch.group(1).split('_')))

				# Register it with bottle
				self.route(
					sUri,
					[ sMethod, 'OPTIONS' ],
					_Route(
						getattr(self.instance, sFunc),	# The function to call
						uri = (lists and sMethod == 'GET') and sUri or None
					)
				)

		# If we have a request for a list of requests
		if lists:

			# If it's True
			if lists is True:
				lists = { '/__list': service }

			# Go through each request in the list
			for sUri in lists:

				# Add the list read route
				self.route(
					sUri,
					[ 'GET', 'OPTIONS' ],
					_Route(True)
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