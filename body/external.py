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
import jsonb
import undefined

# Python imports
from http.cookies import SimpleCookie
from time import sleep

# Pip imports
import requests

# Local imports
from body import errors
from body.info import service_info
from body.request import Request
from body.response import Error, Response
from body.rest import set_session_cookie
from body.service import _instances
from body.shared import ActionType

__action_to_method = {
	'create': requests.post,
	'delete': requests.delete,
	'read': requests.get,
	'update': requests.put
}
"""Map actions to request methods"""

# Get cookie info and make sure we get updates
__cookie = None
def _get_cookie():
	global __cookie
	__cookie = config.body.rest.cookie(False)
config.on_reload(_get_cookie)
_get_cookie()

def create(service: str, path: str, req: Request = undefined) -> Response:
	"""Create

	Make a POST request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (Request): The request details, 'data', 'session', and 'meta'

	Returns:
		Response
	"""
	return request(service, 'create', path, req)

def delete(service: str, path: str, req: Request = undefined) -> Response:
	"""Delete

	Make a DELETE request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (Request): The request details, 'data', 'session', and 'meta'

	Returns:
		Response
	"""
	return request(service, 'delete', path, req)

def read(service: str, path: str, req: Request = undefined) -> Response:
	"""Read

	Make a GET request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (Request): The request details, 'data', 'session', and 'meta'

	Returns:
		Response
	"""
	return request(service, 'read', path, req)

def request(
	service: str,
	action: ActionType,
	path: str,
	req: Request = undefined
) -> Response:
	"""Request

	Method to convert REST requests into HTTP requests

	Arguments:
		service (str): The service we are requesting data from
		action (str): The action to take on the service
		path (str): The path of the request
		req (Request): The request details, 'data', 'session', and 'meta'

	Raises:
		KeyError: if the service or action don't exist

	Return:
		Response
	"""

	# If the request is undefined
	if req == undefined:
		req = Request()

	# If we got a service instance
	if service in _instances:

		# Call the service directly and return the instance
		return _instances[service].request(path, action, req)

	# Else, this is an external service
	else:

		# Get the service info
		info = service_info(service)

		# Init the data and headers
		data = ''
		headers = { }

		# Add the default content length and type
		headers['Content-Length'] = '0'
		headers['Content-Type'] = 'application/json; charset=utf-8'

		# If the data was passed
		if getattr(req, 'data', None):

			# Convert the data to JSON and store the length
			data = jsonb.encode(req.data)
			headers['Content-Length'] = str(len(data))

		# If we have a session, add the ID to the headers
		if getattr(req, 'session', None):
			headers['Authorization'] = (
				isinstance(req.session, str)
				and req.session
				or req.session.key()
			)

		# If we received any meta vars
		if getattr(req, 'meta', None):
			for k,v in req.meta.items():
				headers[f'X-Body-{k}'] = v

		# Loop requests so we don't fail just because of a network hiccup
		attempts = 0
		while True:

			# Increase the attempts
			attempts += 1

			# Make the request using the services URL and the current path
			try:
				response = __action_to_method[action](
					info['url'] + path,
					data = data,
					headers = headers
				)

				# If the request wasn't successful
				if response.status_code != 200:

					# If we got a 401
					if response.status_code == 401:
						return Response.from_json(response.content)
					else:
						return Error(
							errors.SERVICE_STATUS,
							f'{response.status_code}: {response.content}'
						)

				# If we got the wrong content type
				if response.headers['Content-Type'].lower() != \
					'application/json; charset=utf-8':
					return Error(
						errors.SERVICE_CONTENT_TYPE,
						response.headers['content-type']
					)

				# If we have a session cookie value
				if __cookie:

					# Check if it was created
					if 'Set-Cookie' in response.headers:

						# Convert the string to a cookies object
						oCookies = SimpleCookie()
						oCookies.load(response.headers['Set-Cookie'])

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
				return Response.from_json(response.text)

			# If we couldn't connect to the service
			except requests.ConnectionError as e:

				# If we haven't exhausted attempts
				if attempts < 3:

					# Wait for a second
					sleep(1)

					# Loop back around
					continue

				# We've tried enough, return an error
				return Error(errors.SERVICE_UNREACHABLE, str(e))

def update(service: str, path: str, req: Request = undefined) -> Response:
	"""Update

	Make a PUT request

	Arguments:
		service (str): The service to call
		path (str): The path on the service
		req (Request): The request details, 'data', 'session', and 'meta'

	Returns:
		Response
	"""
	return request(service, 'update', path, req)