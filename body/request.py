# coding=utf8
""" Request

Holds the class that holds Request messages sent to Service requests
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2026-10-15"

# Ouroboros imports
import jobject
import jsonb
from memory import _Memory
import undefined

# Python imports
from typing import MutableMapping

class RequestException(Exception):
	pass

class Request(object):
	"""Request

	Represents a standard set of data to any/all requests
	"""

	data: jobject
	""" data member """

	session: _Memory | str
	""" session member """

	meta: jobject
	""" meta member """

	def __init__(self,
		data: MutableMapping = undefined,
		session: _Memory | str = undefined,
		meta: MutableMapping = undefined
	):
		"""Constructor

		Instantiates a new Request

		Arguments:
			data (MutableMapping): The data associated with the request
			session (memory._Memory): The session associated with the request
			meta (MutableMapping): The meta data associated with the request

		Returns:
			Request
		"""

		# Set each member only if it was explicitly passed
		for name, value in (
			( 'data', data ),
			( 'meta', meta ),
			( 'session', session )
		):
			if value is not undefined:
				setattr(self, name, value)

	def __getattr__(self, name):
		"""Get Attr(ibute)

		Magic method to catch missing members and raise an exception. Never
		returns successfully.

		Arguments:
			name (str): The name of the attribute requested

		Raises:
			AttributeError
		"""

		# If it's a valid member
		if name in [ 'data', 'meta', 'session' ]:
			raise RequestException(name)
		raise AttributeError(name)

	def __repr__(self) -> str:
		"""repr

		Returns a readable string representation of the instance, showing only
		the fields that are actually set. Useful for debugging and logging.

		Returns:
			str
		"""
		fields = ', '.join(
			f'{k}={self.__dict__[k]!r}'
			for k in ( 'data', 'session', 'meta' )
			if k in self.__dict__
		)
		return f'{self.__class__.__name__}({fields})'

	def to_dict(self):
		"""To Dict

		Converts the Response into a dict

		Returns:
			dict
		"""

		# Return as a dict
		return {
			k: self.__dict__[k]
			for k in ( 'data', 'meta', 'session' )
			if k in self.__dict__
		}

	def to_json(self, indent: int | str | None = None):
		"""To JSON

		Returns a JSON representation of the object

		Arguments:
			indent (str | int | None): The indentation

		Returns:
			str
		"""
		return jsonb.encode(self.to_dict(), indent)