# coding=utf8
""" Response

Holds the class that holds Response messages sent back from Service Rerquests
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

# Ouroboros imports
import jsonb
import undefined

class Response(object):
	"""Response

	Represents a standard result from any/all requests
	"""

	def __init__(self,
		data: any = undefined,
		error: any = undefined,
		warning: any = undefined
	):
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

		# If there's no data
		if data is not undefined:
			self.data = data
		else:
			self.data = None

		# If there's an error, figure out what type
		if error is not undefined:

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
				raise ValueError('error', 'invalid value: %s' % str(error))

		# Else, set it to False
		else:
			self.error = False

		# If there's a warning, store it as is
		if warning is not undefined:
			self.warning = warning

	def __bool__(self):
		"""bool

		Python magic method to return a bool from the instance. In the case of
		response, True is returned if there's data, else False

		Returns:
			boolean
		"""
		try: return self.data != None
		except AttributeError: return False

	def __repr__(self):
		"""repr

		Python magic method to return a string from the instance that can be
		turned back into the instance

		Returns:
			str
		"""
		return str(self.to_dict())

	def __str__(self):
		"""str

		Python magic method to return a string from the instance

		Returns:
			str
		"""
		return str(self.to_dict())

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

		# If there's data (more likely to be there, so try/except)
		try:
			o.data = val['data']
		except KeyError:
			o.data = None

		# If there's an error (less likely, use if/in)
		if 'error' in val:
			o.error = val['error']
		else:
			o.error = False

		# If there's a warning (less likely, use if/in)
		if 'warning' in val:
			o.warning = val['warning']

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
		try: d = jsonb.decode(val)
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

		# Set the data key if it's set in the instance
		if self.data is not None:
			dRet['data'] = self.data

		# If the error is not set to False
		if self.error is not False:
			dRet['error'] = self.error

		# Look for a warning attribute (less likely, use if/hasattr)
		if hasattr(self, 'warning'):
			dRet['warning'] = self.warning

		# Return the dict
		return dRet

	def to_json(self):
		"""To JSON

		Returns a JSON representation of the object

		Returns:
			str
		"""
		return jsonb.encode(self.to_dict())

	def warning_exists(self):
		"""Warning Exists

		Returns True if there is a warning in the Response

		Returns:
			bool
		"""
		return hasattr(self, 'warning')

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

		# Set the data to None
		self.data = None

		# Set the error code
		self.error = {
			'code': code,
			'msg': msg
		}

class ResponseException(Exception):
	"""Response Exception

	Python won't let you raise anything that doesn't extend BaseException
	"""

	def __init__(self,
		data: any = undefined,
		error: any = undefined,
		warning: any = undefined
	):
		"""Constructor

		Creates a new instance of the Exception

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