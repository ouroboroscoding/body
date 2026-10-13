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
import config
from jobject import jobject
import jsonb

# Python imports
from http.cookies import SimpleCookie
from time import sleep

# Pip imports
import requests
from typing import MutableMapping

# Local imports
from body import errors
from body.info import service_info
from body.response import Error, Response
from body.rest import set_session_cookie
from body.service import _instances

__action_to_request = {
	'create': requests.post,
	'delete': requests.delete,
	'read': requests.get,
	'update': requests.put
}
"""Map actions to request methods"""

# Get cookie info
__cookie = config.body.rest.cookie(False)

def create(service: str, path: str, req: MutableMapping = {}) -> Response:
	"""Create

	Make a POST request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'

	Returns:
		Response
	"""
	return request(service, 'create', path, req)

def delete(service: str, path: str, req: MutableMapping = {}) -> Response:
	"""Delete

	Make a DELETE request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'

	Returns:
		Response
	"""
	return request(service, 'delete', path, req)

def read(service: str, path: str, req: MutableMapping = {}) -> Response:
	"""Read

	Make a GET request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'

	Returns:
		Response
	"""
	return request(service, 'read', path, req)

def request(
	service: str,
	action: str,
	path: str,
	req: MutableMapping = {}
) -> Response:
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

	# If we got a service instance
	if service in _instances:

		# Call the service directly and return the instance
		return _instances[service].request(path, action, jobject(req))

	# Else, this is an external service
	else:

		# Get the service info
		dInfo = service_info(service)

		# Init the data and headers
		sData = ''
		dHeaders = { }

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

		# If we received any meta vars
		if 'meta' in req and req['meta']:
			for k,v in req['meta'].items():
				dHeaders[f'X-Body-{k}'] = v

		# Loop requests so we don't fail just because of a network hiccup
		iAttempts = 0
		while True:

			# Increase the attempts
			iAttempts += 1

			# Make the request using the services URL and the current path
			try:
				oRes = __action_to_request[action](
					dInfo['url'] + path,
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
							f'{oRes.status_code}: {oRes.content}'
						)

				# If we got the wrong content type
				if oRes.headers['Content-Type'].lower() != \
					'application/json; charset=utf-8':
					return Error(
						errors.SERVICE_CONTENT_TYPE,
						oRes.headers['content-type']
					)

				# If we have a session cookie value
				if __cookie:

					# Check if it was created
					if 'Set-Cookie' in oRes.headers:

						# Convert the string to a cookies object
						oCookies = SimpleCookie()
						oCookies.load(oRes.headers['Set-Cookie'])

						# If the session cookie exists
						if __cookie in oCookies:

							# Fetch it
							oCookie = oCookies[__cookie]

							# Create the cookie ourselves
							sMaxAge = oCookie['max-age']
							set_session_cookie(
								oCookie.value,
								int(sMaxAge) if sMaxAge else 0
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

def update(service: str, path: str, req: MutableMapping = {}) -> Response:
	"""Update

	Make a PUT request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (dict): The request details, which can include 'data' and 'session'

	Returns:
		Response
	"""
	return request(service, 'update', path, req)