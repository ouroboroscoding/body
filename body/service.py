# coding=utf8
""" Service

Holds the class used to create services that can be started as rest apps
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

# Ouroboros imports
from tools import evaluate

# Python imports
import abc

# Module imports
from body.errors import DATA_FIELDS
from body.response import ResponseException

class Service(abc.ABC):
	"""Service

	The object to build all services from
	"""

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

	@abc.abstractmethod
	def reset(self):
		"""Reset

		Called when the system has been reset, usually by loading new data that
		the instance will need to process/reprocess

		Returns:
			None
		"""
		raise NotImplementedError('Must implement the "reset" method')