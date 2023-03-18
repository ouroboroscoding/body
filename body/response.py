# coding=utf8
""" Response

Holds the class that holds Response messages sent back from Service Rerquests
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

class Response(object):
	"""Response

	Represents a standard result from any/all requests
	"""

	def __init__(self, data = None, error = None, warning = None):
		"""Constructor

		Initialises a new Response instance

		Arguments:
			data (mixed): If a request returns data this should be set
			error (mixed): If a request has an error, this can be filled with
				a code and message string
			warning (mixed): If a request returns a warning this should be set

		Raises:
			ValueError

		Returns:
			Response
		"""

		# If there's data, store it as is
		if data is not None:
			self.data = data

		# If there's an error, figure out what type
		if error is not None:

			# If we got an int, it's a code with no message string
			if isinstance(error, int):
				self.error = {'code': error, 'msg': ''}

			# If we got a string, it's a message with no code
			elif isinstance(error, str):
				self.error = {'code': 0, 'msg': error}

			# If it's a tuple, 0 is a code, 1 is a message
			elif isinstance(error, tuple):
				self.error = {'code': error[0], 'msg': error[1]}

			# If we got a dictionary, assume it's already right
			elif isinstance(error, dict):
				self.error = error

			# If we got an exception
			elif isinstance(error, Exception):

				# If we got another Response in the Exception, store the error
				#	from it
				if isinstance(error.args[0], Response):
					self.error = error.args[0].error

				# Else, try to pull out the code and message
				else:
					self.error = {'code': error.args[0], 'msg': ''}
					if len(error.args) > 1: self.error['msg'] = error.args[1]

			# Else, we got something invalid
			else:
				raise ValueError('error')

		# If there's a warning, store it as is
		if not warning is None:
			self.warning = warning

	def __str__(self):
		"""str

		Python magic method to return a string from the instance

		Returns:
			str
		"""

		# Create a temp dict
		dRet = {}

		# If there's data
		try: dRet['data'] = self.data
		except AttributeError: pass

		# If there's an error
		try: dRet['error'] = self.error
		except AttributeError: pass

		# If there's a warning
		try: dRet['warning'] = self.warning
		except AttributeError: pass

		# Convert the dict to JSON and return it
		return JSON.encode(dRet)

	def data_exists(self):
		"""Data Exists

		Returns True if there is data in the Response

		Returns:
			bool
		"""
		try: return self.data != None
		except AttributeError: return False

	def error_exists(self):
		"""Error Exists

		Returns True if there is an error in the Response

		Returns:
			bool
		"""
		try: return self.error != None
		except AttributeError: return False

	@classmethod
	def from_dict(cls, val):
		"""From Dict

		Converts a dict back into an Response

		Arguments:
			val (dict): A valid dict

		Returns:
			Response
		"""

		# Create a new instance
		o = cls()

		# If there's data
		try: o.data = val['data']
		except KeyError: pass

		# If there's an error
		try: o.error = val['error']
		except KeyError: pass

		# If there's a warning
		try: o.warning = val['warning']
		except KeyError: pass

		# Return the instance
		return o

	@classmethod
	def from_json(cls, val):
		"""From JSON

		Tries to convert a string made from str() back into an Response

		Arguments:
			val (str): A valid JSON string

		Returns:
			Response
		"""

		# Try to convert the string to a dict
		try: d = JSON.decode(val)
		except ValueError as e: raise ValueError('val', str(e))
		except TypeError as e: raise ValueError('val', str(e))

		# Return the fromDict result
		return cls.from_dict(d)

	def to_dict(self):
		"""To Dict

		Converts the Response into a dict

		Returns:
			dict
		"""

		# Init the return
		dRet = {}

		# Look for a data attribute
		try: dRet['data'] = self.data
		except AttributeError: pass

		# Look for an error attribute
		try: dRet['error'] = self.error
		except AttributeError: pass

		# Look for a warning attribute
		try: dRet['warning'] = self.warning
		except AttributeError: pass

		# Return the dict
		return dRet

	def warning_exists(self):
		"""Warning Exists

		Returns True if there is a warning in the Response

	Returns:
			bool
		"""
		try: return self.warning != None
		except AttributeError: return False

class Error(Response):
	"""Error

	Shorthand form of Response(error=)
	"""

	def __init__(self, code, msg=None):
		"""Constructor

		Initialises a new Response instance

		Arguments:
			code (uint): The error code
			msg (mixed): Optional message for more info on the error

		Returns:
			Error
		"""

		# Set the error code
		self.error = {
			'code': code,
			'msg': msg
		}

class ResponseException(Exception):
	"""Response Exception

	Stupid python won't let you raise anything that doesn't extend BaseException
	"""

	def __init__(self, data = None, error = None, warning = None):
		"""Constructor

		Dumb dumb python

		Arguments:
			data (mixed): If a request returns data this should be set
			error (mixed): If a request has an error, this can be filled with
				a code and message string
			warning (mixed): If a request returns a warning this should be set

		Returns:
			ResponseException
		"""

		# If we got a Response object
		if isinstance(data, Response):
			super().__init__(data)

		# Else, construct the Response and pass it to the parent
		else:
			super().__init__(Response(data, error, warning))
