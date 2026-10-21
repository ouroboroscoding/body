# coding=utf8
""" Request

Holds the class that holds Request messages sent to Service requests
"""
from __future__ import annotations

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
from warnings import warn

class RequestException(AttributeError):
	"""Request Exception

	Handles if a Request attribute is requested and doesn't exist

	Extends:
		AttributeError
	"""
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

	def __contains__(self, name: str) -> bool:
		"""Contains

		Magic method to allow older code to still do checks like

		`if 'data' in request:`

		For when request was a jobject/dict

		Arguments:
			name (str): The member to check for

		Returns:
			bool
		"""
		return name in self.__dict__

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

	def __setattr__(self, name, value):
		"""Set Attr(ibute)

		Catch bad values being set to the instance

		Arguments:
			name (str): The name of the attribute to set
			value (any): The value to set to the name

		Raises:
			ValueError
		"""

		# If we got data
		if name == 'data':

			# Convert it to a jobject at whatever level
			value = jobject.convert(value)

		# Else, if we got a session
		elif name == 'session':

			# If it's not a _Memory or a str it's invalid
			if not isinstance(value, ( _Memory, str )):
				raise ValueError(name)

		# Else, if we got meta data
		elif name == 'meta':

			# If it's not already a jobject
			if not isinstance(value, jobject):

				# If it's a dict, convert
				if isinstance(value, dict):
					value = jobject(value)

				# Else, it's invalid
				else:
					raise ValueError(name)

		# Else, invalid attribute
		else:
			warn(
				f'unexpected attribute {name!r} on Request',
				stacklevel = 2
			)

		# Set the attribute
		object.__setattr__(self, name, value)

	@classmethod
	def from_dict(cls, value: dict) -> Request:
		"""From Dict

		Converts a regular dict to a Request instance

		Arguments:
			value (dict): The dict to convert

		Returns:
			Request
		"""
		return cls(**value)

	def loggable(self) -> dict:
		"""Loggable

		Similar to `to_dict`, but only returns the key of the session

		Returns:
			dict
		"""
		ret = { }
		if 'data' in self.__dict__:
			ret['data'] = self.__dict__['data']
		if 'meta' in self.__dict__:
			ret['meta'] = self.__dict__['meta']
		if 'session' in self.__dict__:
			ret['session'] = (
				isinstance(self.__dict__['session'], _Memory)
				and self.__dict__['session'].key()
				or self.__dict__['session']
			)
		return ret

	def to_dict(self):
		"""To Dict

		Converts the Response into a dict

		Returns:
			dict
		"""

		# Return as a dict by converting each key to a dict
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