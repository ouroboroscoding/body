# coding=utf8
""" Service

Holds the class used to create services that can be started as rest apps
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

__all__ = [ 'Service' ]

# Ouroboros imports
from tools import evaluate

# Python imports
import abc
from collections.abc import Callable
from datetime import datetime
import re
from typing import List

# Module imports
from body.errors import (
	DATA_FIELDS, SERVICE_ACTION, SERVICE_NO_DATA, SERVICE_NO_META,
	SERVICE_NO_SESSION, SERVICE_NO_SUCH_NOUN
)
from body.info import service_info
from body.logging import close_logger, create_logger
from body.request import Request, RequestException
from body.response import Error, Response, ResponseException
from body.rest import REST
from body.shared import ActionType, LogLevelMapper, LogLevelType

_instances = { }
""" Holds the instances of services that have been instantiated """

class Service(abc.ABC):
	"""Service

	The object to build all services from
	"""

	__noun_regex = re.compile(
		r'([a-z]+(?:_[a-z]+)*)_(create|delete|read|update)'
	)
	"""Regular Expression to match to valid service noun method"""

	additional_routes: List[tuple] | None = None
	"""Additional Routes

	Additional URIs can be passed to the server to handle things outside of
	the Service architecture.

	class SomeService(Service):
		pass

	def custom():
		return "<html />"

	SomeService.additional_routes = [ ( '/custom', 'GET', custom ) ]
	"""

	__member_to_error = {
		'data': SERVICE_NO_DATA,
		'meta': SERVICE_NO_META,
		'session': SERVICE_NO_SESSION
	}
	"""Maps missing request member calls to error codes"""

	def __init__(self):
		"""Constructor

		Initialises the service

		Returns:
			Service
		"""

		# If the key already exists
		if self._service_name in _instances:
			raise RuntimeError(
				'Duplicate service name or duplicate instance of the same '
				f'service {self._service_name}'
			)

		# Create the logger
		self._logger = create_logger(self._service_name)

		# Logging
		self.log('debug', 'initialising')

		# Add the service
		_instances[self._service_name] = self

		# Init the list of available methods
		self._requests = { }

		# Go through all the methods found on the service
		for method in dir(self):

			# Check the format of the method name
			oMatch = self.__noun_regex.match(method)

			# If it's a match
			if oMatch:

				# Generate the URL
				sUri = oMatch.group(1).replace('_', '/')

				# Store the url and action
				try:
					self._requests[sUri][oMatch.group(2)] = getattr(self, method)
				except KeyError:
					self._requests[sUri] = {
						oMatch.group(2): getattr(self, method)
					}

		# Call reset
		self.reset()

	def __init_subclass__(cls, **kwargs):
		"""Init Subclass

		Handles setting up sub/child class information on definition
		"""

		# Call the parent method
		super().__init_subclass__(**kwargs)

		# Set the service name
		cls._service_name = cls.__name__.lower()

	@staticmethod
	def check_data(data: dict, fields: list):
		"""Check Data

		Checks if `fields` are set in the `data` dictionary. Raises a \
		DATA_FIELDS ResponseException if any of the `fields` or sub-fields are \
		missing

		\# Check '_id' and 'name' exist in req.data

		check_data(req.data, [ '_id', 'name' ])

		\# Check '_id' and 'record.name' exist in req.data

		check_data(req.data, [ '_id', { 'record': [ 'name' ]} ])

		\# Check 'record.name', and 'options.raw' exist in req.data

		check_data(req.data, {
			'record': [ 'name' ],
			'options': [ 'raw' ]
		})

		Arguments:
			data (dict): The dict to check for missing fields
			fields (list | dict): The list of fields to check for

		Raises:
			ResponseException
		"""

		# Check the data
		try:
			evaluate(data, fields)
		except ValueError as e:
			raise ResponseException(error = (
				DATA_FIELDS,
				[ [ f, 'missing' ] for f in e.args ]
			))

	def log(self, level: LogLevelType, msg: str):
		"""Log

		Writes a message to the log or stdout

		Arguments:
			level (str): The level of the log message
			msg (str): The message to write to the log
		"""

		# Add the timestamp and level
		_msg = f'{datetime.now()} {level.upper()} {self._service_name} {msg}'

		if self._logger:
			self._logger.log(LogLevelMapper[level], _msg)
		else:
			print(_msg)

	def request(self, noun: str, action: ActionType, req: Request) -> Response:
		"""Request

		Called with a noun / action in order to call the appropriate method
		associated. Created to simplify and standardise calls whether from
		internal instances or from REST requests.

		Arguments:
			noun (str): The noun being called in the request
			action (ActionType): The type of request being made
			req (Request): The associated request data

		Raises:
			ResponseException

		Returns:
			Response
		"""

		# Logging
		self.log('info', 'REQUEST %s %s %s' % (
			action,
			noun,
			req.to_json(2)
		))

		# Init, no function
		f = None

		# Try to find the method
		try:
			f = self._requests[noun][action]

		# If we got a KeyError
		except KeyError as e:
			if e.args[0] == noun:
				oResponse = Error(SERVICE_NO_SUCH_NOUN)
			elif e.args[0] == action:
				oResponse = Error(SERVICE_ACTION)
			else:
				raise e

		# If we have a function
		if f:

			# Try to call the method
			try:
				response = f(req)

			# If we got a request member error
			except RequestException as e:
				response = Error(self.__member_to_error[e.args[0]])

			# If we got a response exception, return the Response
			except ResponseException as e:
				response = e.args[0]

		# Logging
		self.log('info', 'RESPONSE %s %s %s' % (
			action,
			noun,
			response.to_json(2)
		))

		# Return the response
		return response

	@classmethod
	def service_name(cls) -> str:
		"""Service Name

		Returns the name of the service, which is just the class name in all
		lowercase.

		Returns:
			str
		"""
		return cls._service_name

	def shutdown(self):
		"""Shutdown

		Should be called when the Service is no longer needed, either before
		it is removed from memory, or before the interpreter closes completed
		"""

		# Logging
		self.log('debug', 'shutting down')

		# Shut down the logger
		close_logger(self._service_name)
		self._logger = None

	@abc.abstractmethod
	def reset(self):
		"""Reset

		Called when the system has been reset, usually by loading new data that
		the instance will need to process/reprocess

		Returns:
			None
		"""
		raise NotImplementedError('Must implement the "reset" method')

	@classmethod
	def rest(cls, on_errors: Callable | None = None):
		"""Rest

		Creates a REST instance using the service as the only internally
		accessible one.

		Arguments:
			on_errors (callable): An optional callback for when a service
				request crashes
		"""

		# Get the service info
		dInfo = service_info(cls._service_name)

		# Create the REST server using the Client instance and run it
		REST(
			services = [ cls ],
			on_errors = on_errors
		).run(
			host = dInfo['host'],
			port = dInfo['port'],
			workers = dInfo['workers'],
			timeout = 'timeout' in dInfo and dInfo['timeout'] or 30
		)