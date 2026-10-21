# coding=utf8
"""REST

Extends Service to allow for launching as an http accesible rest
service
"""
from __future__ import annotations

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-17"

# Limit exports
__all__ = [ 'bottle', 'REST' ]

# Make sure we patched
from gevent import signal_handler, monkey, Timeout as GTimeout
if not monkey.is_module_patched('socket'):
	raise RuntimeError(
		'gevent monkey patching was not applied before importing this '
		'module. Call gevent.monkey.patch_all() as the very first line of '
		'your entrypoint.'
	)

# Ouroboros imports
import config
import jobject
import jsonb
import memory

# Python imports
from collections.abc import Callable
from copy import copy
import re
from signal import getsignal, SIGTERM
import sys
import traceback
from typing import TYPE_CHECKING

# Pip imports
import bottle
from gevent.pool import Pool
from gevent.pywsgi import LoggingLogAdapter, WSGIHandler, WSGIServer

# Local imports
from body import cookie_auth
from body.errors import (
	REST_AUTHORIZATION, REST_CONTENT_TYPE, REST_LIST_TO_LONG, REST_REQUEST_DATA,
	SERVICE_CRASHED, SERVICE_NO_DATA, SERVICE_NO_SESSION
)
from body.logging import close_logger, create_logger, get_logger, log, LogLevel
from body.request import Request
from body.response import Error, Response, ResponseException
from body.shared import ActionType, MethodType
if TYPE_CHECKING:
	from body.service import Service

class _BaseRoute(object):
	"""Base Route

	Handles shared info used in all routes, like service name, uri, and cors
	info

	Extends:
		object
	"""

	__content_type = re.compile(r'^application\/json; charset=utf-?8$')
	"""Valid Content-Type"""

	__cors = None
	"""CORs regular expression"""

	__key_to_errors = {
		'data': SERVICE_NO_DATA,
		'session': SERVICE_NO_SESSION
	}
	"""Maps key error variables to their response error code"""

	__on_error = None
	"""On Error
	Function called when a service request raises an exception
	"""

	def __init__(self, service: Service, uri: str):
		"""Constructor

		Initialises an instance of the Base Route

		Arguments:
			service (Service): The instance of the service associated with this
				route
			uri (str): The path without the service name to the request

		Returns:
			_BaseRoute
		"""

		# Store the service and uri
		self._service = service
		self._uri = uri

	@classmethod
	def auth(cls, req: Request):
		"""Auth

		Handles checking for Auth and adding the session to the request object
		if there is one.

		Arguments:
			req (Request): The request object
		"""

		# Check for auth
		cookie = False
		auth = False

		# Do we have a session cookie value?
		auth = cookie_auth.get()
		if auth:
			cookie = True
			log('rest', LogLevel.DEBUG, 'Authorization from cookie')

		# Else, If the request sent a authorization token
		elif 'Authorization' in bottle.request.headers:
			auth = bottle.request.headers['Authorization']
			log('rest', LogLevel.DEBUG, 'Authorization from header')

		# If we have an auth token
		if auth:

			# Attempt to get the session using the found token
			session = memory.load(auth)

			# If the session is found
			if session:

				# If we have a cookie
				if cookie:

					# Extend the cookie
					cookie_auth.set(auth, session.ttl())

				# Extend the session itself
				session.extend()

				# Add it to the request
				req.session = session

			# Else, session has expired / been deleted
			else:

				# Logging
				log('rest', LogLevel.INFO, f'session expired "{auth}"')

				# If we had a cookie, delete it
				if cookie:
					cookie_auth.clear()

				# Return the response as 401
				bottle.response.status = 401
				raise ResponseException(error = (
					REST_AUTHORIZATION, 'Unauthorized'
				))

	def cors(self) -> bool:
		"""CORS

		Handles CORS requests

		Returns:
			bool
		"""

		# If CORS is enabled
		if self.__cors:

			# Logging
			log('rest', LogLevel.DEBUG, 'CORS check')

			# If the origin matches
			if(
				'origin' in bottle.request.headers and
				self.__cors.match(bottle.request.headers['origin'])
			):

				# Add the current origin as acceptable
				bottle.response.headers['Access-Control-Allow-Origin'] = (
					bottle.request.headers['origin']
				)
				bottle.response.headers['Access-Control-Allow-Credentials'] = (
					'true'
				)
				bottle.response.headers['Vary'] = 'Origin'

			# Invalid origin
			else:

				# Logging
				log('rest', LogLevel.DEBUG, 'CORS origin mismatch')

	def data(self, req: Request):
		"""Data

		Adds the data to the request if there is any

		Arguments:
			req (Request): The associated request object
		"""

		# If we got a Read request and the data is in the GET
		if bottle.request.method == 'GET' and 'd' in bottle.request.query:

			# Convert the GET and store the data
			try:
				req.data = jsonb.decode(bottle.request.query['d'])
			except Exception as e:
				log('rest', LogLevel.ERROR,
					f'{self._uri} received bad ?d=' +
					str(bottle.request.query['d'])
				)
				raise RestException(Error(
					REST_REQUEST_DATA,
					'%s\n%s' % ( bottle.request.query['d'], str(e) )
				))

		# Else we most likely got the data in the body
		else:

			# Make sure the request sent JSON
			try:
				if not self.__content_type.match(
					bottle.request.headers['Content-Type'].lower()
				):
					log('rest', LogLevel.ERROR,
						f'{self._uri} received bad Content-Type ' +
						bottle.request.headers['Content-Type']
					)
					raise RestException(Error(REST_CONTENT_TYPE))
			except KeyError:
				log('rest', LogLevel.ERROR,
					f'{self._uri} received no Content-Type'
				)
				raise RestException(Error(REST_CONTENT_TYPE))

			# Store the data, if it's too big we need to read it rather than
			#	use getvalue
			try:
				data = bottle.request.body.getvalue()
			except AttributeError as e:
				data = bottle.request.body.read()

			# Make sure we have a string, not a set of bytes
			try:
				data = data.decode()
			except (UnicodeDecodeError, AttributeError):
				pass

			# Convert the data and store it
			try:
				if data:
					req.data = jsonb.decode(data)
			except Exception as e:
				log('rest', LogLevel.ERROR,
					f'{self._uri} received bad body ' +
					str(data).replace('\n', '\\n')
				)
				raise RestException(Error(
					REST_REQUEST_DATA,
					'%s\n%s' % ( data, str(e) )
				))

	def meta(self, req: Request):
		"""Meta

		Checks headers for meta info and adds it to the request.

		Arguments:
			req (Request): The associated request object
		"""

		# Step through all headers
		for k in bottle.request.headers:
			if k[0:7] == 'X-Body-':
				try:
					req.meta[k[7:]] = bottle.request.headers[k]
				except AttributeError:
					req.meta = jobject({ k[7:]: bottle.request.headers[k] })

	def on_error(self, req: Request):
		"""On Error

		Called when there's an exception in the route

		Arguments:
			req (Request): The associated request object
		"""

		# Get the traceback info
		error = traceback.format_exc()

		# Logging
		log('rest', LogLevel.ERROR, f'\n{error}')

		# If we have an error handler
		if self.__on_error:

			# Gather all the details, including optional ones
			details = {
				'service': self._service,
				'method': bottle.request.method,
				'path': bottle.request.path,
				'environment': bottle.request.environ,
				'traceback': error
			}

			# Turn the request into a dict
			request = req.to_dict()
			for s in [ 'data', 'session', 'meta' ]:
				if request.get(s, None):
					details[s] = request[s].to_dict()

			# Pass the details to the error handler
			self.__on_error(details)

		# Logging
		log('rest', LogLevel.CRITICAL,
			f'{bottle.request.method} {bottle.request.path} '
			f'CRASHED "{error.replace("\n", "\\n")}"'
		)

		# Return a response of service/request crashed
		return Error(
			SERVICE_CRASHED,
			'%s:%s' % ( self._service.service_name(), bottle.request.path )
		)

	def response_error(self, req: Request, res: Response):
		"""Response Error

		Checks for an error in the response

		Arguments:
			res (Response): The response object to check / modify if necessary
		"""

		# If the response contains an error
		if res.error:

			# If it's an authorization error
			if res.error['code'] == REST_AUTHORIZATION:

				# Set the http status to 401 Unauthorized
				bottle.response.status = 401

				# If the message is missing
				if res.error['msg'] == '':
					res.error['msg'] = 'Unauthorized'

			# Add the service and path to the call
			l = [
				self._service.service_name(),
				bottle.request.method,
				bottle.request.path,
				req.to_dict()
			]
			try:
				res.error['service'].append(l)
			except KeyError:
				res.error['service'] = [ l ]

	@classmethod
	def set_cors(cls, cors: re.Pattern):
		"""CORs

		Sets the regular expression used to validate domains making requests

		Arguments:
			pattern (re.Pattern): A compiled regular expression
		"""
		cls.__cors = cors

	@classmethod
	def set_on_error(cls, callback: callable):
		"""On Error

		Sets the global error handling function

		Arguments:
			callback (callable): The function to call with the error details

		Returns:
			None
		"""
		cls.__on_error = staticmethod(callback)

class _ListRoute(_BaseRoute):
	"""List Route

	A private callable class used to store list rest routes

	Extends:
		_BaseRoute
	"""

	def __call__(self):
		"""Call (__call__)

		Python magic method that allows the instance to be called

		Returns:
			str
		"""

		# Cors
		self.cors()

		# Set the return to JSON
		bottle.response.headers['Content-Type'] = (
			'application/json; charset=utf-8'
		)

		# Initialise the request instance
		req = Request()

		# In case the service crashes
		try:

			# Get data
			self.data(req)

			# Check for auth / session
			self.auth(req)

			# Check for meta
			self.meta(req)

			# If the data isn't passed or isn't an array
			if 'data' not in req or not isinstance(req.data, list):
				log('rest', LogLevel.ERROR,
					f'{self._uri} received bad data {str(req.data)}'
				)
				response = Error(
					REST_REQUEST_DATA,
					'data must be an array / list'
				)

			# Else, if it's beyond the max
			elif len(req.data) > 10:
				log('rest', LogLevel.WARNING,
					f'{self._uri} received too much data {str(req.data)}'
				)
				response = Error(
					REST_LIST_TO_LONG,
					f'Can not request more than 10 urls via {self._uri}'
				)

			# Else, we have an array of nouns to call and return
			else:

				# Logging
				log('rest', LogLevel.INFO,
					f'REQUEST {self._uri}', req.to_dict()
				)

				# Init the responses
				responses = [ ]

				# Go through each element in the list
				for m in req.data:

					# If we got a string
					if isinstance(m, str):
						m = [ m ]

					# Else, if we didn't get a list
					elif not isinstance(m, list):
						log('rest', LogLevel.WARNING,
							f'{self._uri}:{m[0]} received bad data {str(m)}'
						)
						response = Error(
							REST_REQUEST_DATA, [ m, (
								'data must be an array / list of URI(0) and '
								'DATA(1), or single string for the URI'
							) ]
						)
						break

					# Copy the __list request data so that the session and meta
					#	is shared. We will overwrite / delete the data based on
					#	what was sent for the specific URI
					request = copy(req)

					# If unique data was passed for the child request, set it
					#	to the request
					if len(m) == 2:
						request.data = m[1]

					# No unique data was sent, so we need to delete the
					#	original data from the request
					else:
						del request.data

					# Call the request and append the data to the
					#	response
					try:
						responses.append([
							m[0],
							self._service.request(
								m[0],
								'read',
								request
							).to_dict()
						])

					# If there's any sort of crash
					except Exception as e:

						# Generate the response with the specific request
						responses.append(
							self.on_error(request)
						)

				# Else, we got through the list
				else:

					# Set the response using the list of individual
					#	responses
					response = Response(responses)

		# If we got a Response Exception
		except ResponseException as e:

			# Set the response
			response = e.args[0]

		# If we get absolutely any exception
		except Exception as e:

			# Generate the response
			response = self.on_error(req)

		# Check for response error
		self.response_error(req, response)

		# Logging
		log('rest', LogLevel.INFO, f'RESPONSE {self._uri}', response.to_dict())

		# Return the Response as a string
		return response.to_json()

class _Optionroute(_BaseRoute):
	"""Options Route

	Handles OPTIONS requests

	Extends:
		_BaseRoute
	"""

	def __init__(self,
		service: Service,
		uri: str,
		options: list[MethodType]
	):
		"""Constructor

		Initialises an instance of the route

		Arguments:
			service (Service): The instance of the service associated with this
				route
			uri (str): The path without the service name to the request
			methods (list[MethodType]): The type of methods allowed

		Returns:
			_OptionsRoute
		"""

		# Call the parent
		super(_Optionroute, self).__init__(service, uri)

		# Store the action
		self._options = ', '.join(options)

	def __call__(self):
		"""Call (__call__)

		Python magic method that allows the instance to be called

		Returns:
			str
		"""

		# Logging
		log('rest', LogLevel.INFO, f'CORS {self._uri}')

		# Call shared cors
		self.cors()

		# Set the default headers expected for OPTIONS
		bottle.response.headers['Access-Control-Allow-Methods'] = self._options
		bottle.response.headers['Access-Control-Max-Age'] = 1728000
		bottle.response.headers['Access-Control-Allow-Headers'] = (
			'Authorization,DNT,X-CustomHeader,Keep-Alive,User-Agent,'
			'X-Requested-With,If-Modified-Since,Cache-Control,Content-Type'
		)
		bottle.response.headers['Content-Type'] = 'text/plain charset=UTF-8'
		bottle.response.headers['Content-Length'] = 0
		bottle.request.status = 204

		# Return an empty string
		return ''

class _RequestRoute(_BaseRoute):
	"""Route

	A private callable class used to store request rest routes

	Extends:
		_BaseRoute
	"""

	__method_to_action = {
		'POST': 'create',
		'DELETE': 'delete',
		'GET': 'read',
		'PUT': 'update'
	}
	"""Maps HTTP methods to service actions"""

	def __init__(self,
		service: Service,
		uri: str,
		action: ActionType
	):
		"""Constructor

		Initialises an instance of the route

		Arguments:
			service (Service): The instance of the service associated with this
				route
			uri (str): The path without the service name to the request
			action (ActionType): The type of action requested

		Returns:
			_RequestRoute
		"""

		# Call the parent
		super(_RequestRoute, self).__init__(service, uri)

		# Store the action
		self._action = action

	def __call__(self):
		"""Call (__call__)

		Python magic method that allows the instance to be called

		Returns:
			str
		"""

		# Cors
		self.cors()

		# Set the return to JSON
		bottle.response.headers['Content-Type'] = (
			'application/json; charset=utf-8'
		)

		# Initialise the request details
		req = Request()

		# Check for rest exceptions
		try:

			# Get data
			self.data(req)

			# Check for auth / session
			self.auth(req)

			# Check for meta
			self.meta(req)

			# In case the service crashes
			try:

				# Call the appropriate API method based on the HTTP/request
				#	method
				response = self._service.request(
					self._uri,
					self.__method_to_action[bottle.request.method],
					req
				)

			# If we get absolutely any exception
			except Exception as e:

				# Set the response
				response = self.on_error(req)

		# If we got a response exception
		except ResponseException as e:

			# Set the response using the exceptions first argument
			response = e.args[0]

		# Handle REST issue
		except RestException as e:

			# Store the response
			response = e.args[0]

		# Check for an error on the response
		self.response_error(req, response)

		# Return the response as json
		return response.to_json()

class RestException(Exception):
	"""Rest Exception

	Used to handle failures during the request

	Extends:
		Exception
	"""
	pass

class REST(bottle.Bottle):
	"""REST

	Used to access a service instance via HTTP/REST

	Extends:
		Bottle
	"""

	__instantiated = False
	""" Prevents duplicates """

	__action_to_method = {
		'create': 'POST',
		'delete': 'DELETE',
		'read': 'GET',
		'update': 'PUT'
	}
	""" Maps service actions to HTTP methods """

	def __init__(self,
		services: list[type[Service]],
		on_errors: Callable | None = None
	):
		"""Constructor

		Creates a new REST instance

		Arguments:
			services (dict): The service classes to instantiate and use
			on_errors (callable): Optional, a function to call when a service
				request throws an exception

		Raises:
			ValueError

		Returns:
			RestService
		"""

		# If we're already instantiated
		if self.__instantiated:
			raise RuntimeError('REST can only be instantiated once')
		self.__instantiated = True

		# If the services are not a list
		if not isinstance(services, list):
			raise TypeError(
				'services must be a list', sys._getframe().f_code.co_name
			)

		# Call the parent constructor first so the object is setup
		super(REST, self).__init__()

		# Create the logger instance
		create_logger('rest')

		# Get necessary config values
		conf = config.body.rest({
			'allowed': [ 'localhost' ],
			'lists': True,
			'monitor': None
		})

		# If cors
		cors = False
		if conf['allowed']:
			cors = True

			# If it's a string
			if isinstance(conf['allowed'], str):
				allowed = str(conf['allowed']).replace('.', '\\.')

			# Else, if it's a list
			if isinstance(conf['allowed'], list):

				# If we only have one
				if len(conf['allowed']) == 1:
					allowed = str(conf['allowed'][0]).replace('.', '\\.')

				# Else, convert the list into a grouping of possible values
				else:
					allowed = '(?:%s)' % '|'.join([
						str(s).replace('.', '\\.')
						for s in conf['allowed']
					])

			# Else, it's invalid
			else:
				raise RuntimeError(
					'config.body.rest.allowed must be a string or list of '
					'strings'
				)

			# Generate the full regex
			sRegex = f'https?://(.*\\.)?{allowed}'

			# Logging
			log('rest', LogLevel.DEBUG, f'CORS: {sRegex}')

			# Compile the regex and set it
			_BaseRoute.set_cors(re.compile(sRegex))

		# If we have an error handler
		if on_errors:
			_BaseRoute.set_on_error(on_errors)

		# If we have a cookie name, log it
		cookie = cookie_auth.name()
		if cookie:
			log('rest', LogLevel.DEBUG, f'session cookie: {cookie}')

		# Add the monitor path if needed
		if conf['monitor'] is not None:

			# Create the check method
			check = ( lambda u, p: u == conf['monitor'][0] and
									p == conf['monitor'][1] )

			# Route
			route = (
				(len(conf['monitor']) < 3 or conf['monitor'][2] is True)
					and '/__monitor'
					or f'/{conf['monitor'][2]}'
			)
			log('rest', LogLevel.DEBUG, f'GET {route[1:]} added')

			# Add the route
			self.route(route, 'GET', bottle.auth_basic(check)(self.monitor))

		# Init the service instances
		self._instances: list[type[Service]] = [ ]

		# Step through each service
		one_service = len(services) == 1
		for service in services:

			# Create the instances
			service = service()

			# Go through all the request methods found in the service
			for uri,actions in service._requests.items():

				# Generate the route
				route = (
					one_service
					and f'/{uri}'
					or f'/{service.service_name()}/{uri}'
				)

				# Init the list of methods
				if cors:
					methods = [ ]

				# Go through the actions
				for action in actions:

					# Get the method
					method = self.__action_to_method[action]

					# Add it to the list
					if cors:
						methods.append(method)

					# Register it with bottle
					self.route(
						route,
						method,
						_RequestRoute(service, uri, action)
					)

					# Logging
					log('rest', LogLevel.DEBUG,
						f'{method} {service.service_name()}/{uri} added'
					)

				# If cors
				if cors:

					# Add the OPTIONS route
					self.route(
						route, 'OPTIONS', _Optionroute(service, uri, methods)
					)

					# Logging
					log('rest', LogLevel.DEBUG,
						f'OPTIONS {service.service_name()}/{uri} added'
					)

			# If we have additional static routes
			if service.additional_routes is not None:

				# Go through each one
				for l in service.additional_routes:

					# Generate the route
					route = (
						one_service
						and l[0]
						or f'/{service.service_name()}{l[0]}'
					)

					# Generate the route
					self.route(route, l[1], l[2])

					# Logging
					log('rest', LogLevel.DEBUG,
						f'{l[1]} /{service.service_name()}{l[0]} added'
					)

					# cors
					if cors:

						# Add the OPTIONS
						self.route(
							route,
							'OPTIONS',
							_Optionroute(service, uri, l[1])
						)

						# Logging
						log('rest', LogLevel.DEBUG,
							f'OPTIONS {service.service_name()}/{uri} added'
						)

			# If we have a request for a list of requests
			if conf['lists']:

				# If it's True, use __lists, else use the string sent
				_list = (
					conf['lists'] is True
						and '__list'
						or str(conf['lists'])
				)

				# Generate the route
				route = (
					one_service
					and _list
					or f'/{service.service_name()}/{_list}'
				)

				# Add the list read route
				self.route(
					route,
					'GET',
					_ListRoute(service, _list)
				)

				# Logging
				log('rest', LogLevel.DEBUG,
					f'GET {service.service_name()}/{_list} added'
				)

				# cors
				if cors:

					# Add the OPTIONS
					self.route(
						route,
						'OPTIONS',
						_Optionroute(service, _list, [ 'GET' ])
					)

					# Logging
					log('rest', LogLevel.DEBUG,
						f'OPTIONS {service.service_name()}/{_list} added'
					)

		# Add the instance to the list
		self._instances.append(service)

	# monitor method
	def monitor(self) -> str:
		"""Monitor

		Displays data relevant to the webserver

		Returns:
			str
		"""

		# Get used pool
		i = self._pool.size - self._pool.free_count()

		# If we have a pool
		sPool = (
			self._pool
			and f'{i} / {self._pool.size}'
			or 'No pool'
		)

		# Return the info
		return (f'Pool used: {sPool}\n')

	# run method
	def run(self,
		host = '127.0.0.1',
		port = 8080,
		maxfile = 20971520,
		workers = 100,
		timeout = 30
	):
		"""Run

		Overrides Bottle's run to default gunicorn and other fields

		Arguments:
			host (str): Server address to bind to
			port (int): Server port to bind to
			debug (bool): Debug mode
			maxfile (int): Maximum size of requests
			workers (uint): The pool of concurrent connections
			timeout (uint): The maximum time for any request

		Returns:
			None
		"""

		# Set the max file size
		bottle.BaseRequest.MEMFILE_MAX = maxfile

		# Set debug mode
		bottle.debug(True)

		# Construct the gevent Pool
		self._pool = Pool(size = workers)

		# Set the timeout
		TimeoutHandler.timeout_seconds = timeout

		# Create the WSGI server with the given host/port/pool
		server = WSGIServer(
			(host, port),
			self,
			spawn = self._pool,
			handler_class = TimeoutHandler,
			log = LoggingLogAdapter(
				get_logger('rest'),
				level = LogLevel.DEBUG
			)
		)

		# If we want to see the start info
		log('rest', LogLevel.DEBUG,
			f'REST serving on http://{host}:{port} '
			f'(concurrency limited to {workers})'
		)

		# Check for an existing signal handler
		prev_handler = getsignal(SIGTERM)

		# Catch sigterm and kill the server so we can exit gracefully
		def _sigterm_handler(signum = None, frame = None):
			server.stop()
			if callable(prev_handler):
				try:
					prev_handler(signum, frame)
				except TypeError:
					prev_handler()

		# Attach the signal handler to SIGTERM
		signal_handler(SIGTERM, _sigterm_handler)

		# Run the webserver
		try:
			server.serve_forever()
		except KeyboardInterrupt:
			server.stop()

		# Shutdown the instances
		for o in self._instances:
			o.shutdown()

		# Close the logger
		close_logger('rest')

class TimeoutHandler(WSGIHandler):
	"""Timeout Handler

	Overrides WSGIHandler in order to be able to set a timeout explicitly

	Extends:
		WSGIHandler
	"""

	timeout_seconds = None
	"""Timeout Seconds"""

	def handle(self):
		"""Handle

		Handles any request
		"""

		# If we don't have a timeout, default to regular handle
		if self.timeout_seconds is None:
			return super().handle()

		# Set the gevent Timeout
		self._timeout = GTimeout.start_new(self.timeout_seconds)

		# Handle the request
		try:
			super().handle()
		finally:
			self._timeout.cancel()

	def handle_error(self, t, v, tb):
		"""Handle Error

		Called if there's any error in the handling of a request
		"""

		# Check if the event if the timeout
		if getattr(self, '_timeout', None) is v:
			try:
				self.start_response('504 Gateway Timeout',
									[('Content-Type', 'text/plain')])
				self.write(b'Request timed out\n')
			except Exception:
				pass

		# Else, default to regular handle_error
		else:
			super().handle_error(t, v, tb)