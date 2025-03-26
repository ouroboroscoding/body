# coding=utf8
"""Body

Shared methods for accessing the brain and other shared formats
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2022-08-29"

__all__ = [
	'constants', 'Error', 'errors', 'regex', 'register_services', 'Response',
	'ResponseException', 'REST', 'Service'
]

# Ouroboros imports
from config import config
import jsonb
import undefined

# Python imports
from copy import copy
from sys import stderr
from time import sleep

# Pip imports
import requests

# Local imports
from . import constants, errors, locations, regex, response, rest, service

# Error, Response, and ResponseException
Error = response.Error
Response = response.Response
ResponseException = response.ResponseException

# REST and Config
REST = rest.REST
Locations = locations.Locations

# Service
Service = service.Service

__services = {}
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

def register_services(running: dict = undefined) -> Locations:
	"""Register Services

	Takes a dictionary of services to their urls for use by the request
	functions

	Arguments:
		running (dict): Optional, dict of local running services

	Returns:
		body.locations.Locations
	"""

	# Pull in the global services
	global __services

	# Init the REST config
	oLocations = Locations(config.body.rest({
		'allowed': None,
		'default': {
			'domain': 'localhost',
			'host': '0.0.0.0',
			'port': 9000,
			'protocol': 'http',
			'workers': 1
		}
	}))

	# Rest the dict
	__services = {}

	# Go through each config
	for s in oLocations:

		# If the service exists locally
		if running and s in running:
			__services[s] = running[s]

		# Else, add the URL
		else:
			__services[s] = oLocations[s]['url']

	# Return the config
	return oLocations

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

	# Loop requests so we don't fail just because of a network glitch
	iAttempts = 0
	while True:

		# Increase the attempts
		iAttempts += 1

		# If we got a service instance
		if isinstance(__services[service], Service):
			print('Can not currently call local services', file = stderr)

		# Else, this is an external service
		else:

			# Make the request using the services URL and the current path, then
			#	store the response
			try:
				oRes = __action_to_request[action][0](
					__services[service] + path,
					data=sData,
					headers=dHeaders
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

				# Success, break out of the loop
				break

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

	# Else turn the content into a Response and return it
	return Response.from_json(oRes.text)

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