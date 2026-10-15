# coding=utf8
"""Info

Generates and stores service info
"""
from __future__ import annotations

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2026-10-13"

# Ouroboros imports
import config

# Python imports
from copy import copy

__info = None
"""Service Info"""

def _generate_info():
	"""Generate Info

	Fetches the service information from the config and generates the URLs for
	all available services
	"""

	# Pull in the global services
	global __info

	# Fetch the REST config
	conf = config.body.rest({
		'allowed': None,
		'default': {
			'domain': 'localhost',
			'host': '0.0.0.0',
			'port': 9000,
			'protocol': 'http',
			'workers': 1
		}
	})

	# If we didn't get a list of services
	if 'services' not in conf:
		raise ValueError('config.body.rest.services is missing')

	# Init the defaults if none are found
	if 'defaults' not in conf:
		conf['defaults'] = { }

	# Port values are not modified by default
	port_mod = 0

	# If there is a port modifier
	if 'port' in conf['default']:

		# Make sure it's an integer
		try:
			port_mod = int(conf['default']['port'])
			del conf['default']['port']
		except ValueError:
			raise ValueError('config.body.rest.default.port', 'must be an int')

	# Reset the dict of services
	__info = { }

	# Loop through the list of services in the rest config
	for s in conf['services']:

		# If the service doesn't point to a dict
		if not isinstance(conf['services'][s], dict):
			raise ValueError(
				'config.body.rest.services.%s' % s, 'must be a dict'
			)

		# Start with the default values
		parts = conf['default'].copy()

		# Then add the service values
		parts.update(conf['services'][s])

		# If we have no port
		if 'port' not in parts:

			# But we have a modifier, assume we add to 80
			if port_mod: parts['port'] = 80 + port_mod

		# Else add the modifier to the port passed
		else:
			parts['port'] += port_mod

		# Set defaults for any missing parts
		if not parts['protocol']: parts['protocol'] = 'http'
		if not parts['domain']: parts['domain'] = 'localhost'
		if 'path' not in parts: parts['path'] = ''
		else: parts['path'] = '%s/' % str(parts['path'])

		# Store the parts for the service
		__info[s] = parts.copy()

		# Generate a URL from the parts and store it
		__info[s]['url'] = '%s://%s%s/%s' % (
			parts['protocol'],
			parts['domain'],
			'port' in parts and ":%d" % parts['port'] or '',
			parts['path']
		)

		# If we still have no port, default to 80
		if 'port' not in __info[s]:
			__info[s]['port'] = 80

def service_info(name: str) -> dict:
	"""Service Info

	Returns the info related to a specific service

	Arguments:
		name (str): The name of the service

	Raises:
		KeyError if the name doesn't match a service

	Returns:
		dict
	"""

	global __info

	# If we haven't already, generate the list of services
	if __info is None:
		_generate_info()

	# Return a shallow copy of the info for the service
	return copy(__info[name])