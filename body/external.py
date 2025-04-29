# coding=utf8
"""External

Methods to connecting to external services via http
"""
from __future__ import annotations

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2025-04-06"

__all__ = [
	'create', 'delete', 'read', 'register_service', 'request', 'service_info',
	'update'
]

# Ouroboros imports
from config import config
from jobject import jobject
import jsonb
import undefined

# Python imports
from copy import copy
from time import sleep

# Pip imports
import requests
from typing import TYPE_CHECKING

# Local imports
from body import errors
from body.response import Error, Response, ResponseException
if TYPE_CHECKING:
	from body.service import Service

__services = None
"""Registered Services"""

__action_to_request = {
	'create': [ requests.post, 'POST' ],
	'delete': [ requests.delete, 'DELETE' ],
	'read': [ requests.get, 'GET' ],
	'update': [ requests.put, 'PUT' ]
}
"""Map actions to request methods"""

def create(
	service: str,
	path: str,
	req: dict = {},
	headers: dict = undefined
):
	"""Create

	Make a POST request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'
		headers (dict): Any additional headers to add to the request

	Returns:
		Response
	"""
	return request(service, 'create', path, req, headers)

def delete(
	service: str,
	path: str,
	req: dict = {},
	headers: dict = undefined
):
	"""Delete

	Make a DELETE request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'
		headers (dict): Any additional headers to add to the request

	Returns:
		Response
	"""
	return request(service, 'delete', path, req, headers)

def read(
	service: str,
	path: str,
	req: dict = {},
	headers: dict = undefined
):
	"""Read

	Make a GET request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'
		headers (dict): Any additional headers to add to the request

	Returns:
		Response
	"""
	return request(service, 'read', path, req, headers)

def register_service(name: str, instance: Service):
	"""Register Service

	Marks a service as internal so that any create, read, update, delete request
	will call the local instance instead of attempting an http request

	Arguments:
		name (str): The name of the service and how others will contact it
		instance (Service): The created instance of the servce
	"""

	global __services

	# If we haven't already, generate the list of services
	if __services is None:
		_generate_services()

	# Add the instance and init the paths
	__services[name]['instance'] = instance
	__services[name]['paths'] = {}

	# Go through all the request methods in the service
	for dMethod in instance.requests:

		# Generate the URL
		sUri = dMethod['name'].replace('_', '/')

		# Store the url and action
		try:
			__services[name]['paths'][sUri][dMethod['action']] = dMethod['func']
		except KeyError:
			__services[name]['paths'][sUri] = {
				dMethod['action']: dMethod['func']
			}

	# Return the service
	return __services[name]

def _generate_services():
	"""Generate Services

	Fetches the service information from the config and generates the URLs for
	all available services
	"""

	# Pull in the global services
	global __services

	# Fetch the REST config
	dRest = config.body.rest({
		'allowed': None,
		'default': {
			'domain': 'localhost',
			'host': '0.0.0.0',
			'port': 9000,
			'protocol': 'http',
			'workers': 1
		}
	})

	# If we didn't get a list of services
	if 'services' not in dRest:
		raise ValueError('config.body.rest.services', 'missing')

	# Init the defaults if none are found
	if 'defaults' not in dRest:
		dRest['defaults'] = {}

	# Port values are not modified by default
	iPortMod = 0

	# If there is a port modifier
	if 'port' in dRest['default']:

		# Make sure it's an integer
		try:
			iPortMod = int(dRest['default']['port'])
			del dRest['default']['port']
		except ValueError:
			raise ValueError('config.body.rest.default.port', 'must be an int')

	# Reset the dict of services
	__services = {}

	# Loop through the list of services in the rest config
	for s in dRest['services']:

		# If the service doesn't point to a dict
		if not isinstance(dRest['services'][s], dict):
			raise ValueError(
				'config.body.rest.services.%s' % s, 'must be a dict'
			)

		# Start with the default values
		dParts = dRest['default'].copy()

		# Then add the service values
		dParts.update(dRest['services'][s])

		# If we have no port
		if 'port' not in dParts:

			# But we have a modifier, assume we add to 80
			if iPortMod: dParts['port'] = 80 + iPortMod

		# Else add the modifier to the port passed
		else:
			dParts['port'] += iPortMod

		# Set defaults for any missing parts
		if not dParts['protocol']: dParts['protocol'] = 'http'
		if not dParts['domain']: dParts['domain'] = 'localhost'
		if 'path' not in dParts: dParts['path'] = ''
		else: dParts['path'] = '%s/' % str(dParts['path'])

		# Store the parts for the service
		__services[s] = dParts.copy()

		# Generate a URL from the parts and store it
		__services[s]['url'] = '%s://%s%s/%s' % (
			dParts['protocol'],
			dParts['domain'],
			'port' in dParts and ":%d" % dParts['port'] or '',
			dParts['path']
		)

		# If we still have no port, default to 80
		if 'port' not in __services[s]:
			__services[s]['port'] = 80

def request(
	service: str,
	action: str,
	path: str,
	req: dict = {},
	headers: dict = undefined
):
	"""Request

	Method to convert REST requests into HTTP requests

	Arguments:
		service (str): The service we are requesting data from
		action (str): The action to take on the service
		path (str): The path of the request
		req (dict): The request details: 'data', 'session', and 'enviroment'
		headers (dict): Any additional headers to add to the request

	Raises:
		KeyError: if the service or action don't exist

	Return:
		Response
	"""

	global __services

	# If we haven't already, generate the list of services
	if __services is None:
		_generate_services()

	# Init the data and headers
	sData = ''
	dHeaders = (headers is not undefined and isinstance(headers, dict)) and \
				copy(headers) or \
				{}

	# Add the default content length and type
	dHeaders['Content-Length'] = '0'
	dHeaders['Content-Type'] = 'application/json; charset=utf-8'

	# If the data was passed
	if 'data' in req and req['data']:

		# Convert the data to JSON and store the length
		sData = jsonb.encode(req['data'])
		dHeaders['Content-Length'] = str(len(sData))

	# If we have a session, add the ID to the headers
	if 'session' in req and req['session']:
		dHeaders['Authorization'] = req['session'].key()

	# If we got a service instance
	if 'instance' in __services[service]:

		# Try to call the method
		try:
			f = __services[service]['paths'][path][action]

		# If we got a KeyError
		except KeyError as e:
			if e.args[0] == path:
				return Error(errors.SERVICE_NO_SUCH_NOUN)
			elif e.args[0] == action:
				return Error(errors.SERVICE_ACTION)
			else:
				raise e

		# Try to call the method
		try:
			return f(jobject(req))

		# If we got a KeyError
		except (AttributeError, KeyError) as e:
			if e.args[0] == 'data':
				return Error(errors.SERVICE_NO_DATA)
			elif e.args[0] == 'session':
				return Error(errors.SERVICE_NO_SESSION)
			else:
				raise e

		# If we got a response exception, return the Response
		except ResponseException as e:
			return e.args[0]

	# Else, this is an external service
	else:

		# Loop requests so we don't fail just because of a network hiccup
		iAttempts = 0
		while True:

			# Increase the attempts
			iAttempts += 1

			# Make the request using the services URL and the current path, then
			#	store the response
			try:
				oRes = __action_to_request[action][0](
					__services[service]['url'] + path,
					data = sData,
					headers = dHeaders
				)

				# If the request wasn't successful
				if oRes.status_code != 200:

					# If we got a 401
					if oRes.status_code == 401:
						return Response.from_json(oRes.content)
					else:
						return Error(
							errors.SERVICE_STATUS,
							'%d: %s' % (oRes.status_code, oRes.content)
						)

				# If we got the wrong content type
				if oRes.headers['Content-Type'].lower() != \
					'application/json; charset=utf-8':
					return Error(
						errors.SERVICE_CONTENT_TYPE,
						'%s' % oRes.headers['content-type']
					)

				# Turn the content into a Response and return it
				return Response.from_json(oRes.text)

			# If we couldn't connect to the service
			except requests.ConnectionError as e:

				# If we haven't exhausted attempts
				if iAttempts < 3:

					# Wait for a second
					sleep(1)

					# Loop back around
					continue

				# We've tried enough, return an error
				return Error(errors.SERVICE_UNREACHABLE, str(e))

def service_info(name: str) -> dict:
	"""Service Info

	Returns the info related to a specific service

	Arguments:
		name (str): The name of the service

	Raises:
		KeyError if the name doesn't match a service

	Returns:
		dict
	"""

	global __services

	# If we haven't already, generate the list of services
	if __services is None:
		_generate_services()

	# Return a shallow copy of the info for the service
	return copy(__services[name])

def update(
	service: str,
	path: str,
	req: dict = {},
	headers: dict = undefined
):
	"""Update

	Make a PUT request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'
		headers (dict): Any additional headers to add to the request

	Returns:
		Response
	"""
	return request(service, 'update', path, req, headers)