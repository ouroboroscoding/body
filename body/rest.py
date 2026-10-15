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
__all__ = [ 'bottle', 'clear_session_cookie', 'REST', 'set_session_cookie' ]

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
from tools import clone
import undefined

# Python imports
from collections.abc import Callable
import logging
import re
from signal import getsignal, SIGTERM
import sys
import traceback
from typing import TYPE_CHECKING

# Pip imports
import bottle
from gevent.pool import Pool
from gevent.pywsgi import WSGIHandler, WSGIServer

# Local imports
from body.constants import SECONDS_365_DAYS
from body.errors import \
	REST_AUTHORIZATION, REST_CONTENT_TYPE, REST_LIST_INVALID_URI, \
	REST_LIST_TO_LONG, REST_REQUEST_DATA, SERVICE_CRASHED, SERVICE_NO_DATA, \
	SERVICE_NO_SESSION
from body.response import Error, Response, ResponseException
from body.shared import ActionType
if TYPE_CHECKING:
	from body.service import Service

# Global vars
_cookie = undefined

class _BaseRoute(object):
	"""Base Route

	Handles shared info used in all routes, like service name, uri, and cors
	info

	Extends:
		object
	"""

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
	def auth(cls, req: jobject):
		"""Auth

		Handles checking for Auth and adding the session to the request object
		if there is one.

		Arguments:
			req (jobject): The request object
		"""

		# Check for auth
		cookie = False
		auth = False

		# Do we have a session cookie name and was it sent?
		if _cookie and bottle.request.cookies.get(_cookie, False):
			cookie = True
			auth = bottle.request.cookies[_cookie]

		# Else, If the request sent a authorization token
		elif 'Authorization' in bottle.request.headers:
			auth = bottle.request.headers['Authorization']

		# If we have an auth token
		if auth:

			# Get the session from the Authorization token
			req.session = memory.load(auth)

			# If the session is found
			if req.session:

				# If we have a cookie
				if cookie:

					# Extend the cookie
					set_session_cookie(auth, req.session.ttl())

				# Extend the session itself
				req.session.extend()

			# Else, session has expired / been deleted
			else:

				# If we had a cookie, delete it
				if cookie:
					clear_session_cookie()

				# Return the response as 401
				bottle.response.status = 401
				return Error(
					REST_AUTHORIZATION, 'Unauthorized'
				).to_json()

	def cors(self) -> bool:
		"""CORS

		Handles CORS requests

		Returns:
			bool
		"""

		# If CORS is enabled and the origin matches
		if(	self.__cors and
			'origin' in bottle.request.headers and
			self.__cors.match(bottle.request.headers['origin'])
		):

			# Add the current origin as acceptable
			bottle.response.headers['Access-Control-Allow-Origin'] = (
				bottle.request.headers['origin']
			)
			bottle.response.headers['Access-Control-Allow-Credentials'] = 'true'
			bottle.response.headers['Vary'] = 'Origin'

	def meta(self, req: jobject):
		"""Meta

		Checks headers for meta info and adds it to the request.

		Arguments:
			req (jobject): The associated request object
		"""

		# Step through all headers
		for k in bottle.request.headers:
			if k[0:7] == 'X-Body-':
				try:
					req.meta[k[7:]] = bottle.request.headers[k]
				except AttributeError:
					req.meta = jobject({ k[7:]: bottle.request.headers[k] })

	def on_error(self, req: jobject):
		"""On Error

		Called when there's an exception in the route

		Arguments:
			req (jobject): The associated request object
		"""

		# Get the traceback info
		error = traceback.format_exc()

		# Print the traceback to stderr
		self._service.log('error', error)

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
			for s in [ 'data', 'session' ]:
				if s in req:
					details[s] = req[s]

			# Pass the details to the error handler
			self.__on_error(details)

		# Return a response of service/request crashed
		return Error(
			SERVICE_CRASHED,
			'%s:%s' % ( self._service.service_name(), bottle.request.path )
		)

	def response_error(self, res: Response):
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
				bottle.request.path
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

		# Initialise the request details
		req = jobject({ })

		# Convert the GET and store the data
		try:
			req.data = jsonb.decode(bottle.request.query['d'])
		except Exception as e:
			return Error(
				REST_REQUEST_DATA,
				'%s\n%s' % ( bottle.request.query['d'], str(e) )
			).to_json()

		# Check for meta
		self.meta(req)

		# Check for auth
		self.auth(req)

		# In case the service crashes
		try:

			# If the data isn't passed or isn't an array
			if 'data' not in req or not isinstance(req.data, list):
				response = Error(
					REST_REQUEST_DATA,
					'data must be an array'
				)

			# Else, if it's beyond the max
			elif len(req.data) > 10:
				response = Error(
					REST_LIST_TO_LONG,
					f'Can not request more than 10 urls via {self._uri}'
				)

			# Else, we have an array of nouns to call and return
			else:

				# Logging
				self._service.log(
					'debug',
					f'REQUEST {self._uri} {jsonb.encode(req.to_dict(), 2)}'
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
						response = Error(
							REST_REQUEST_DATA, [ m, (
								'data must be an array or URI and data, '
								'or single string for the URI'
							) ]
						)
						break

					# If the URI doesn't exist
					if m[0] not in self.__uris:
						response = Error(REST_LIST_INVALID_URI, m[0])
						break

					# Clone the __list request data so that the session
					#	or any other data is shared
					request = clone(req)

					# If unique data was passed for the child request
					if len(m) == 2:

						# If we didn't get a dict
						if not isinstance(m[1], dict):
							response = Error(
								REST_LIST_INVALID_URI,
								[ m[1], 'data must be an object' ]
							)
							break

						# Set the data for this request
						request.data = m[1]

					# No unique data was sent, so we need to delete the
					#	original data from the request
					else:
						try: del request.data
						except AttributeError: pass

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

					# If we got a KeyError
					except (AttributeError, KeyError) as e:
						if e.args[0] in self.__key_to_errors:
							response = Error(
								self.__key_to_errors[e.args[0]]
							)
							break
						else:
							raise

					# If we got a response exception
					except ResponseException as e:

						# Set the response using the exceptions first argument
						response = e.args[0]
						break

				# Else, we got through the list
				else:

					# Set the response using the list of individual
					#	responses
					response = Response(responses)

		# If we get absolutely any exception
		except Exception as e:

			# Set the response
			response = self.on_error(req)

			# Add the service and path to the call
			l = [
				self.__services[self._service],
				bottle.request.method,
				bottle.request.path
			]
			try:
				response.error['service'].append(l)
			except KeyError:
				response.error['service'] = [ l ]

		# Check for response error
		self.response_error(response)

		# Logging
		self._service.log(
			'debug',
			f'RESPONSE {self._uri} {jsonb.encode(response.to_dict(), 2)}'
		)

		# Return the Response as a string
		return response.to_json()

class _Optionroute(_BaseRoute):
	"""Options Route

	Handles OPTIONS requests

	Extends:
		_BaseRoute
	"""

	def __call__(self):
		"""Call (__call__)

		Python magic method that allows the instance to be called

		Returns:
			str
		"""

		# Logging
		self._service.log('debug', f'CORS {self._uri}')

		# Call shared cors
		self.cors()

		# Set the default headers expected for OPTIONS
		bottle.response.headers['Access-Control-Allow-Methods'] = (
			'DELETE, GET, POST, PUT, OPTIONS'
		)
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

	__content_type = re.compile(r'^application\/json; charset=utf-?8$')
	"""Valid Content-Type"""

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
		req = jobject({ })

		# Check for rest exceptions
		try:

			# If we got a Read request and the data is in the GET
			if bottle.request.method == 'GET' and 'd' in bottle.request.query:

				# Convert the GET and store the data
				try:
					req.data = jsonb.decode(bottle.request.query['d'])
				except Exception as e:
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
						raise RestException(Error(REST_CONTENT_TYPE))
				except KeyError:
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
					if data: req.data = jsonb.decode(data)
				except Exception as e:
					raise RestException(Error(
						REST_REQUEST_DATA,
						'%s\n%s' % ( data, str(e) )
					))

			# Check for meta
			self.meta(req)

			# Check for auth
			self.auth(req)

			# In case the service crashes
			try:

				# Call the appropriate API method based on the HTTP/request
				#	method
				try:
					response = self._service.request(
						self._uri,
						self.__method_to_action[bottle.request.method],
						req
					)

				# If we got a response exception
				except ResponseException as e:

					# Set the response using the exceptions first argument
					response = e.args[0]

			# If we get absolutely any exception
			except Exception as e:

				# Set the response
				response = self.on_error(req)

			# Check for response error
			self.response_error(response)

			# Return the Response as a string
			return response.to_json()

		# Handle Rest issues
		except RestException as e:

			# Log the error
			self._service.log('error', 'RESPONSE %s %s %s' % (
				self._action,
				self._uri,
				jsonb.encode(e.args[0].to_dict(), 2)
			))

			# Return the response
			return e.args[0].to_json()

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

		global _cookie

		# If we're already instantiated
		if self.__instantiated:
			raise RuntimeError('REST can only be instantiated once')
		self.__instantiated = True

		# Call the parent constructor first so the object is setup
		super(REST, self).__init__()

		# If the services are not a list
		if not isinstance(services, list):
			raise TypeError(
				'services must be a list', sys._getframe().f_code.co_name
			)

		# Get necessary config values
		conf = config.body.rest({
			'allowed': [ 'localhost' ],
			'cookie': False,
			'lists': True,
			'monitor': None,
			'verbose': False
		})

		# If cors
		if conf['allowed']:

			# If it's not a list
			if( isinstance(conf['allowed'], str) or
				not isinstance(conf['allowed'], list) ):
				raise RuntimeError('config.body.rest.allowed must be a list')

			# If we only have one
			if len(conf['allowed']) == 1:
				allowed = conf['allowed'][0].replace('.', '\\.')

			# Else, conver the list into a grouping of possible values
			else:
				allowed = '(?:%s)' % '|'.join([
					s.replace('.', '\\.')
					for s in conf['allowed']
				])

			# Generate the full regex
			sRegex = f'https?://(.*\\.)?{allowed}'
			if conf['verbose']:
				print(f'REST CORS: {sRegex}')

			# Compile the regex and set it
			_BaseRoute.set_cors(re.compile(sRegex))

		# If we have an error handler
		if on_errors:
			_BaseRoute.set_on_error(on_errors)

		# If we have a cookie name, set the global var
		_cookie = conf['cookie']
		if _cookie and conf['verbose']:
			print(f'REST session cookie: {_cookie}')

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
			if conf['verbose']:
				print(f'REST {route} route added')

			# Add the route
			self.route(
				route,
				[ 'GET', 'OPTIONS' ],
				bottle.auth_basic(check)(self.monitor)
			)

		# Init the service instances
		self._instances: list[type[Service]] = [ ]

		# Step through each service
		one_service = len(services) == 1
		for service in services:

			# Create the instances
			service_instance = service()

			# Go through all the request methods found in the service
			for uri,actions in service_instance._requests.items():

				# Generate the route
				route = (
					one_service
						and f'/{uri}'
						or f'/{service_instance.service_name()}/{uri}'
				)

				# There's at least one, so add the OPTIONS route
				self.route(
					route, 'OPTIONS', _Optionroute(service_instance, uri)
				)

				# Logging
				print(
					f'REST Route: OPTIONS '
					f'{service_instance.service_name()}/{uri}'
				)

				# Go through the actions
				for action in actions:

					# Get the method
					method = self.__action_to_method[action]

					# Register it with bottle
					self.route(
						route,
						method,
						_RequestRoute(service_instance, uri, action)
					)

					# Logging
					print(
						f'REST Route: {method} '
						f'{service_instance.service_name()}/{uri}'
					)

			# If we have additional static routes
			if service_instance.additional_routes is not None:

				# Go through each one
				for l in service_instance.additional_routes:

					# Generate the route
					route = (
						one_service
						and l[0]
						or f'/{service_instance.service_name()}{l[0]}'
					)

					# Add the OPTIONS
					self.route(
						route,
						'OPTIONS',
						_Optionroute(service_instance, uri)
					)

					# Logging
					print(
						f'REST Route: OPTIONS '
						f'{service_instance.service_name()}/{uri}'
					)

					# Generate the route
					self.route(route, l[1], l[2])

					# Logging
					print(
						f'REST Route: {l[1]} '
						f'/{service_instance.service_name()}{l[0]}'
					)

			# If we have a request for a list of requests
			if conf['lists']:

				# If it's True, use __lists, else use the string sent
				sList = (
					conf['lists'] is True
						and '__list'
						or str(conf['lists'])
				)

				# Generate the route
				route = (
					one_service
					and sList
					or ('/%s/%s' % ( service_instance.service_name(), sList))
				)

				# Add the list read route
				self.route(
					route,
					[ 'GET', 'OPTIONS' ],
					_ListRoute(service_instance, sList)
				)

				# Logging
				if conf['verbose']:
					print(
						'REST Route: GET '
						f'/{service_instance.service_name()}/{sList}'
					)

		# Add the instance to the list
		self._instances.append(service_instance)

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
	def run(self, host = '127.0.0.1', port = 8080, quiet = False,
			plugins = None, debug = False, maxfile = 20971520, workers = 100,
			timeout = 30, **kargs):
		"""Run

		Overrides Bottle's run to default gunicorn and other fields

		Arguments:
			host (str): Server address to bind to
			port (int): Server port to bind to
			quiet (bool): Suppress output to stdout and stderr?
			plugins (list): List of plugins to the server
			debug (bool): Debug mode
			maxfile (int): Maximum size of requests
			workers (uint): The pool of concurrent connections
			timeout (uint): The maximum time for any request

		Returns:
			None
		"""

		# Set the max file size
		bottle.BaseRequest.MEMFILE_MAX = maxfile

		# Install plugins if any
		if plugins:
			self.install(*plugins)
		if debug:
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
			log = None if quiet else logging.getLogger('gevent.wsgi'),
			**kargs
		)

		# If we want to see the start info
		if not quiet:
			print(
				f'REST serving on http://{host}:{port} '
				f'(concurrency limited to {workers})'
			)

		# Check for an existing signal handler
		prev_handler = getsignal(SIGTERM)

		# Catch sigterm and kill the server so we can exit gracefully
		def _sigterm_handler(signum, frame):
			server.stop()
			if callable(prev_handler):
				prev_handler(signum, frame)
		signal_handler(SIGTERM, _sigterm_handler)

		# Run the webserver
		try:
			server.serve_forever()
		except KeyboardInterrupt:
			server.stop()

		# Shutdown the instances
		for o in self._instances:
			o.shutdown()

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

def clear_session_cookie():
	"""Clear Session Cookie

	Deletes the cookie for the session
	"""

	global _cookie

	# If we don't have the cookie value
	if _cookie is undefined:
		_cookie = config.body.rest.cookie(False)

	# If we have no cookie
	if _cookie is False:
		return

	# Delete the cookie
	bottle.response.set_cookie(
		_cookie,
		'',
		max_age = 0,
		path = '/',
		secure = True,
		samesite = 'Lax',
		httponly = True
	)

def set_session_cookie(key, ttl):
	"""Set Session Cookie

	Sets the httpOnly cookie for the session

	Arguments:
		key (str): The session key
		ttl (uint): The time to live for the cookie
	"""

	global _cookie

	# If we don't have the cookie value
	if _cookie is undefined:
		_cookie = config.body.rest.cookie(False)

	# If we have no cookie
	if _cookie is False:
		return

	# If the ttl is 0
	iTTL = ttl or SECONDS_365_DAYS

	# Set the cookie in bottle
	bottle.response.set_cookie(
		_cookie,
		key,
		max_age = iTTL,
		path = '/',
		secure = True,
		samesite = 'Lax',
		httponly = True
	)