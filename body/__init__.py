# coding=utf8
"""Body

Shared methods for accessing the brain and other shared formats
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2022-08-29"

__all__ = [
	'Config', 'constants', 'Error', 'errors', 'regex', 'Response',
	'ResponseException', 'REST', 'Service'
]

# Python imports
from time import sleep

# Pip imports
import jsonb
import requests

# Local imports
from . import	config, \
				constants, \
				errors, \
				regex, \
				response, \
				rest, \
				service

# Error, Response, and ResponseException
Error = response.Error
Response = response.Response
ResponseException = response.ResponseException

# REST and Config
REST = rest.REST
Config = config.Config

# Service
Service = service.Service

__services = {}
"""Registered Services"""

__action_to_request = {
	'create': [requests.post, 'POST'],
	'delete': [requests.delete, 'DELETE'],
	'read': [requests.get, 'GET'],
	'update': [requests.put, 'PUT']
}
"""Map actions to request methods"""

def create(service: str, path: str, req: dict = {}):
	"""Create

	Make a POST request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data',
					'environment', and 'session'

	Returns:
		Response
	"""
	return request(service, 'create', path, req)

def delete(service: str, path: str, req: dict = {}):
	"""Delete

	Make a DELETE request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data',
					'environment', and 'session'

	Returns:
		Response
	"""
	return request(service, 'delete', path, req)

def read(service: str, path: str, req: dict = {}):
	"""Read

	Make a GET request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data',
					'environment', and 'session'

	Returns:
		Response
	"""
	return request(service, 'read', path, req)

def register(conf: dict):
	"""Register

	Takes a dictionary of services to their urls for use by the request
	functions

	Arguments:
		conf (dict): Configuration variables for remote services

	Returns:
		None
	"""

	# Pull in the global services
	global __services

	# Store the urls by service
	__services = { k: v['url'] for k,v in conf.items() }

def request(service: str, action: str, path: str, req: dict = {}):
	"""Request

	Method to convert REST requests into HTTP requests

	Arguments:
		service (str): The service we are requesting data from
		action (str): The action to take on the service
		path (str): The path of the request
		req (dict): The request details: 'data', 'session', and 'enviroment'

	Raises:
		KeyError: if the service or action don't exist

	Return:
		Response
	"""

	# Init the data and headers
	sData = ''
	dHeaders = {
		'Content-Length': '0',
		'Content-Type': 'application/json; charset=utf-8'
	}

	# If the data was passed
	if 'data' in req and req['data']:

		# Convert the data to JSON and store the length
		sData = jsonb.encode(req['data'])
		dHeaders['Content-Length'] = str(len(sData))

	# If we have a session, add the ID to the headers
	if 'session' in req and req['session']:
		dHeaders['Authorization'] = req['session'].id()

	# Loop requests so we don't fail just because of a network glitch
	iAttempts = 0
	while True:

		# Increase the attempts
		iAttempts += 1

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
					return Error(errors.SERVICE_STATUS, '%d: %s' % (oRes.status_code, oRes.content))

			# If we got the wrong content type
			if oRes.headers['Content-Type'].lower() != 'application/json; charset=utf-8':
				return Error(errors.SERVICE_CONTENT_TYPE, '%s' % oRes.headers['content-type'])

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