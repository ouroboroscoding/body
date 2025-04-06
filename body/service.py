# coding=utf8
""" Service

Holds the class used to create services that can be started as rest apps
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

# Ouroboros imports
import config
from tools import evaluate

# Python imports
import abc
from collections.abc import Callable
import re
from typing import List

# Module imports
from body.external import register_service
from body.errors import DATA_FIELDS
from body.response import ResponseException
from body.rest import REST

class Service(abc.ABC):
	"""Service

	The object to build all services from
	"""

	__noun_regex = re.compile(
		r'([a-z]+(?:_[a-z]+)*)_(create|delete|read|update)'
	)
	"""Regular Expression to match to valid service noun method"""

	def __init__(self, name: str | None = None):
		"""Constructor

		Initialises the service

		Arguments:
			name (str): Optional, uses __class__.__name__.lower() if not set.
		Returns:
			Service
		"""

		# Store the name
		self._name = name is None \
			and self.__class__.__name__.lower() \
			or name

		# Init the list of available methods
		self._requests = []

		# Go through all the functions found on the service
		for sFunc in dir(self):

			# Check the format of the method name
			oMatch = self.__noun_regex.match(sFunc)

			# If it's a match
			if oMatch:

				# Add it to the list
				self._requests.append({
					'name': oMatch.group(1),
					'action': oMatch.group(2),
					'func': getattr(self, sFunc)
				})

		# Register the service with body
		self._info = register_service(self._name, self)

		# Call reset
		self.reset()

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

	@property
	def name(self) -> str:
		"""Name

		Returns the name of the service

		Returns:
			str
		"""
		return self._name

	@abc.abstractmethod
	def reset(self):
		"""Reset

		Called when the system has been reset, usually by loading new data that
		the instance will need to process/reprocess

		Returns:
			None
		"""
		raise NotImplementedError('Must implement the "reset" method')

	@property
	def requests(self) -> List[dict]:
		"""Requests

		Returns a list of all the requests available in the service

		Returns:
			dict[]
		"""
		return self._requests

	def rest(self,
		additional: List[list] = None,
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

		# Create the REST server using the Client instance
		oRest = REST(
			instances = [ self ],
			cors = config.body.rest.allowed('localhost'),
			on_errors = on_errors,
			verbose = config.body.rest.verbose(False)
		)

		# If there's any additional
		if additional:
			for l in additional:
				oRest.route(*l)

		# Run the server forever
		oRest.run(
			host = self._info['host'],
			port = self._info['port'],
			workers = self._info['workers'],
			timeout = 'timeout' in self._info and self._info['timeout'] or 30
		)