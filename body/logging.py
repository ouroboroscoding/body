# coding=utf8
""" Logging

Setup and return logging objects
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

__all__ = [ 'close_logger', 'create_logger', 'get_logger', 'log', 'LogLevel' ]

# Ouroboros imports
import config
import jsonb
from tools import combine
import undefined

# Python imports
from datetime import datetime
from enum import IntEnum
import logging
import logging.handlers
import os
import queue
from sys import stderr, stdout

# Keep track of config
_conf = None

# Keep track of all the logger info
_loggers = { }

# Constants
LEVEL_STR_TO_INT = {
	'critical': logging.CRITICAL,
	'debug': logging.DEBUG,
	'error': logging.ERROR,
	'info': logging.INFO,
	'warning': logging.WARNING
}
LEVEL_INT_TO_STR = {
	logging.CRITICAL: 'CRTICAL',
	logging.DEBUG: 'DEBUG',
	logging.ERROR: 'ERROR',
	logging.INFO: 'INFO',
	logging.WARNING: 'WARNING'
}
STD_STR_TO_FILE = {
	'stderr': stderr,
	'stdout': stdout
}

# Types
class LogLevel(IntEnum):
	CRITICAL = logging.CRITICAL
	DEBUG = logging.DEBUG
	ERROR = logging.ERROR
	INFO = logging.INFO
	WARNING = logging.WARNING
"""Simplifies logging levels into a single type"""

def close_logger(name):
	"""Close Logger

	Closes a logger by cleaning up after it

	Arguments:
		name (str): The name of the log
	"""

	# If it doesn't exist, do nothing
	if name not in _loggers:
		return

	# Shut down the listener
	if _loggers[name]['listener']:
		_loggers[name]['listener'].stop()

	# Flush the handler and close it
	if _loggers[name]['handler']:
		_loggers[name]['handler'].flush()
		_loggers[name]['handler'].close()

	# Close the handlers
	if _loggers[name]['logger']:
		for h in list(_loggers[name]['logger'].handlers):
			_loggers[name]['logger'].removeHandler(h)
			h.close()

	# Remove the name
	del _loggers[name]

def create_logger(name: str):
	"""Create Logger

	Creates a new Logger instance in a Queue and returns it

	Arguments:
		name (str): The name of the log
	"""

	# If we didn't get a dict
	if not isinstance(_conf, dict):
		raise ValueError('config.body.logging must be a dict')

	# If we have specific overrides for the name
	if name in _conf['names']:
		if not isinstance(_conf['names'][name], dict):
			raise ValueError(
				f'config.body.logging.names.{name} must be a dict'
			)
		conf = combine(_conf, _conf['names'][name])
	else:
		conf = _conf

	# Get the integer value of the level and handle an invalid value
	level = str(conf['level']).lower()
	try:
		level = LEVEL_STR_TO_INT[level]
	except KeyError:
		raise ValueError(
			'logging:level must be one of "debug", "critical", "error", '
			f'"info", "warning". Received: "{level}"'
		)

	# Check the output type
	if conf['output'] not in ('stdout', 'stderr', 'file'):
		raise ValueError(
			'logging:output must be one of "stdout", "stderr", "file". '
			f'Received: "{level}"'
		)

	# If we are storing to a file
	if conf['output'] == 'file':

		# Init the file data
		file = { }

		# If the file conf is not a dict
		if not isinstance(conf['file'], dict):
			raise ValueError(
				'logging:file must be a dict. '
				f"Received: {str(conf['file'])}"
			)

		# If the backups isn't an unsigned int
		if( not isinstance(conf['file']['backups'], int)
			or conf['file']['backups'] < 0
		):
			raise ValueError(
				'logging:backups must be an unsigned integer. '
				f"Received: {str(conf['file']['backups'])}"
			)
		file['backups'] = conf['file']['backups']

		# Make sure the path is a string
		if not isinstance(conf['file']['path'], str):
			raise ValueError(
				'logging:file.path must be a string. '
				f"Received: \"{str(conf['file']['path'])}\""
			)

		# Trim the path
		file['path'] = conf['file']['path'].strip()

		# If there's any value, and it doesn't end in /, add one
		if file['path']:
			if not file['path'].endswith('/'):
				file['path'] += '/'

		# Check the file path exists if it's not this path (empty string)
		if file['path'] and not os.path.isdir(file['path']):
			raise FileNotFoundError(f'{file['path']} is not a directory')

		# If the name is not a str
		if not isinstance(conf['file']['name'], str):
			raise ValueError(
				'logging:file.name must be a string. '
				f"Received: \"{str(conf['file']['name'])}\""
			)

		# Store the name using it as a template
		file['name'] = conf['file']['name'].replace('{name}', name)

	# Check pretty print
	if not isinstance(conf['pretty_print'], bool):
		raise ValueError(
			'logging:pretty_print must be true or false. '
			f"Received: \"{str(conf['pretty_print'])}\""
		)

	# Init the class instances
	instances = {
		'handler': None,
		'listener': None,
		'logger': None,
		'indent': conf['pretty_print'] and 2 or None
	}

	# Init the queue and listener
	_queue = queue.Queue(-1)

	# Get the logger by service name
	instances['logger'] = logging.getLogger(f'body:{name}')
	if instances['logger'].handlers:
		raise RuntimeError(f'Logger body:{name} already exists.')

	# Set logger level and disable propagation
	instances['logger'].setLevel(level)
	instances['logger'].propagate = False

	# Create the queue handler and assign it
	instances['logger'].addHandler(
		logging.handlers.QueueHandler(_queue)
	)

	# If we are create a file handler
	if conf['output'] == 'file':

		# Create the file handler
		instances['handler'] = logging.handlers.TimedRotatingFileHandler(
			filename = f"{file['path']}{file['name']}",
			when = 'midnight',
			interval = 1,
			backupCount = file['backups'],
			encoding = 'utf-8'
		)

	# Else, we are creating a stream handler
	else:

		# Create the stream handler
		instances['handler'] = logging.StreamHandler(
			STD_STR_TO_FILE[conf['output']]
		)

	# Remove any formatting of the message, we will handle it
	instances['handler'].setFormatter('')

	# Add the listener for the queue
	instances['listener'] = logging.handlers.QueueListener(
		_queue, instances['handler'], respect_handler_level = True
	)
	instances['listener'].start()

	# Add the name to the list of existing
	_loggers[name] = instances

	# Return the actual logger
	return instances['logger']

def get_logger(name: str) -> logging.Logger | None:
	"""Get Logger

	Returns the logger associated with the name if there is one

	Arguments:
		name (str): The name of the logger

	Returns:
		logging.Logger | None
	"""
	try:
		return _loggers[name]['logger']
	except KeyError:
		return None

def _load_config():
	"""Load Config

	Fetches the values from the config
	"""
	global _conf
	_conf = config.body.logging({
		'file': {
			'backups': 30,
			'name': '{name}.log',
			'path': './'
		},
		'level': 'info',
		'names': { },
		'output': 'stdout',
		'pretty_print': False
	})

# Call once to start
_load_config()

def log(name: str, level: LogLevel, msg: str, data: any = undefined):
	"""Log

	Writes a message to the log or stdout

	Arguments:
		name (str): The name of the log
		level (LogLevel): The level of the log message
		msg (str): The message to write to the log
		data (any): Data that will be converted to JSON and appended to the
			message
	"""

	try:
		d = _loggers[name]
	except KeyError:
		print(f'Invalid logger name {name}', file=stderr)

	# Add the data to the message if it was passed
	_msg = (
		data is undefined
		and msg
		or f'{msg} {jsonb.encode(data, d['indent'])}'
	)

	# Write to the log
	d['logger'].log(
		level,
		f'{datetime.now()} [{LEVEL_INT_TO_STR[level]}] {_msg}'
	)

def _reload_loggers():
	"""Reload Loggers

	Called when config is reloaded to make sure we reset the loggers and
	use new settings (even if the settings are the same, it's not worth
	checking)
	"""

	global _conf

	# Reset config
	_load_config()

	# Go through each available name, close, then re-open
	for name in _loggers:
		close_logger(name)
		create_logger(name)

# Reload loggers on config change
config.on_reload(_reload_loggers)