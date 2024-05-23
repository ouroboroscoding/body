# coding=utf8
"""Locations

Configuration for accessing REST services via http
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-17"

class Locations(object):
	"""Locations class

	Represents configuration data for connecting to/loading services
	"""

	def __contains__(self, service):
		"""__contains__

		Python magic method for checking a key exists in a dict like object

		Arguments:
			service (str): The service to check for

		Returns:
			bool
		"""
		return service in self.__services

	def __getitem__(self, service):
		"""__getitem__

		Python magic method for getting a key from a dict like object

		Arguments:
			service (str): The service config to return

		Raises:
			KeyError

		Returns:
			mixed
		"""

		# If it's in services
		try:
			return self.__services[service].copy()

		# Else, throw an exception
		except KeyError:
			raise KeyError(service)

	def __init__(self, conf):
		"""Constructor

		Initialises the instance

		Arguments:
			conf (dict): The configuration data for compiling the list of
				services

		Returns:
			Locations
		"""

		# If we didn't get a dictionary for the service conf
		if not isinstance(conf, dict):
			raise ValueError('conf')

		# If we didn't get a list of services
		if 'services' not in conf:
			raise ValueError('conf.services')

		# Init the defaults if none are found
		if 'defaults' not in conf:
			conf['defaults'] = {}

		# Port values are not modified by default
		iPortMod = 0

		# If there is a port modifier
		if 'port' in conf['default']:

			# Make sure it's an integer
			try:
				iPortMod = int(conf['default']['port'])
				del conf['default']['port']
			except ValueError:
				raise ValueError('conf.default.port must be an int')

		# Initialise the list of services
		self.__services = {}

		# Loop through the list of services
		for s in conf['services']:

			# If the service doesn't point to a dict
			if not isinstance(conf['services'][s], dict):
				raise ValueError('conf.services.%s' % s)

			# Start with the default values
			dParts = conf['default'].copy()

			# Then add the service values
			dParts.update(conf['services'][s])

			# If we have no port
			if 'port' not in dParts:

				# But we have a modifier, assume we add to 80
				if iPortMod: dParts['port'] = 80 + iPortMod

			# Else add the modifier to the port passed
			else:
				dParts['port'] += iPortMod

			# Set defaults for any missing parts
			if not dParts['protocol']: dParts['protocol'] = 'http'
			if not dParts['domain']: dParts['domain'] = 'localhost'
			if 'path' not in dParts: dParts['path'] = ''
			else: dParts['path'] = '%s/' % str(dParts['path'])

			# Store the parts for the service
			self.__services[s] = dParts.copy()

			# Generate a URL from the parts and store it
			self.__services[s]['url'] = '%s://%s%s/%s' % (
				dParts['protocol'],
				dParts['domain'],
				'port' in dParts and ":%d" % dParts['port'] or '',
				dParts['path']
			)

			# If we still have no port, default to 80
			if 'port' not in self.__services[s]:
				self.__services[s]['port'] = 80

	def __iter__(self):
		"""__iter__

		Python magic method to return an iterator for the instance

		Returns:
			iterator
		"""
		return iter(self.__services)

	def __str__(self):
		"""__str__

		Python magic method to return a string for the instance

		Returns:
			str
		"""
		return str(self.__services)

	def keys(self):
		"""services

		Returns the keys (services) in the instance

		Returns:
			str[]
		"""
		return self.__services.keys()