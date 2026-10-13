# coding=utf8
""" Service

Holds the class used to create services that can be started as rest apps
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

# Ouroboros imports
import jobject
import jsonb
from tools import evaluate
import undefined

# Python imports
import abc
from collections.abc import Callable
from datetime import datetime
import re
from typing import List
import warnings

# Module imports
from body.errors import (
	DATA_FIELDS, SERVICE_ACTION, SERVICE_NO_DATA, SERVICE_NO_SESSION,
	SERVICE_NO_SUCH_NOUN
)
from body.info import service_info
from body.response import Error, Response, ResponseException
from body.rest import REST
from body.types import ActionType

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

		# Add the service
		_instances[self._service_name] = self

		# Init the list of available methods
		self._requests = { }

		# Go through all the functions found on the service
		for sFunc in dir(self):

			# Check the format of the method name
			oMatch = self.__noun_regex.match(sFunc)

			# If it's a match
			if oMatch:

				# Generate the URL
				sUri = oMatch.group(1).replace('_', '/')

				# Store the url and action
				try:
					self._requests[sUri][oMatch.group(2)] = getattr(self, sFunc)
				except KeyError:
					self._requests[sUri] = {
						oMatch.group(2): getattr(self, sFunc)
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

	def request(self, noun: str, action: ActionType, req: jobject) -> Response:
		"""Request

		Called with a noun / action in order to call the appropriate method
		associated. Created to simplify and standardise calls whether from
		internal instances or from REST requests.

		Arguments:
			noun (str): The noun being called in the request
			action (ActionType): The type of request being made
			req (jobject): The associated request data

		Raises:
			ResponseException

		Returns:
			Response
		"""

		# Logging
		print('%s REQUEST %s %s %s %s' % (
			str(datetime.now()),
			action,
			self._service_name,
			noun,
			(req and jsonb.encode(req, 2) or 'None')
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
				oResponse = f(req)

			# If we got a KeyError
			except (AttributeError, KeyError) as e:
				if e.args[0] == 'data':
					oResponse = Error(SERVICE_NO_DATA)
				elif e.args[0] == 'session':
					oResponse = Error(SERVICE_NO_SESSION)
				else:
					raise e

			# If we got a response exception, return the Response
			except ResponseException as e:
				oResponse = e.args[0]

		# Logging
		print('%s RESPONSE %s %s %s %s' % (
			str(datetime.now()),
			action,
			self._service_name,
			noun,
			jsonb.encode(oResponse.to_dict(), 2)
		))

		# Return the response
		return oResponse

	@classmethod
	def service_name(cls) -> str:
		"""Service Name

		Returns the name of the service, which is just the class name in all
		lowercase.

		Returns:
			str
		"""
		return cls._service_name

	@abc.abstractmethod
	def reset(self):
		"""Reset

		Called when the system has been reset, usually by loading new data that
		the instance will need to process/reprocess

		Returns:
			None
		"""
		raise NotImplementedError('Must implement the "reset" method')

	def rest(self,
		additional: List[list] = undefined,
		on_errors: Callable | None = None
	):
		"""Rest

		Creates a REST instance using the service as the only internally
		accessible one

		Additional URIs can be passed to the server to handle things outside of
		the Service architecture.

		def custom():
			return "<html />"

		rest(
			additional = [ [ '/custom', 'GET', custom ] ]
		)

		Arguments:
			additional (list): A list of tuples representing arguments to route.
			on_errors (callable): An optional callback for when a service
				request crashes
		"""

		# If deprecated additional argument sent
		if additional is not undefined:
			self.additional_routes = additional
			warnings.warn(
				( 'Setting additional on Service.rest is deprecated and will '
				 'not work in the future. Instead set self.additional_routes '
				 'in Service.__init__' ),
				DeprecationWarning,
				stacklevel = 2
			)

		# Get the service info
		dInfo = service_info(self._service_name)

		# Create the REST server using the Client instance and run it
		REST(
			instances = [ self ],
			on_errors = on_errors
		).run(
			host = dInfo['host'],
			port = dInfo['port'],
			workers = dInfo['workers'],
			timeout = 'timeout' in dInfo and dInfo['timeout'] or 30
		)