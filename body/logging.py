# coding=utf8
""" Logging

Setup and return logging objects
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

__all__ = [ 'close_logger', 'create_logger' ]

# Ouroboros imports
import config

# Python imports
import logging
import logging.handlers
import os
import queue
_
# Body imports
from body.shared import LogLevelMapper

# Keep track of config
_conf = None

# Keep track of all the logger info
_loggers = { }

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
	if _loggers[name]['file_handler']:
		_loggers[name]['file_handler'].flush()
		_loggers[name]['file_handler'].close()

	# Close the handlers
	if _loggers[name]['logger']:
		for h in list(_loggers[name]['logger'].handlers):
			_loggers[name]['logger'].removeHandler(h)
			h.close()

	# Remove the name
	del _loggers[name]

def create_logger(name: str) -> logging.Logger:
	"""Create Logger

	Creates a new Logger instance in a Queue and returns it

	Arguments:
		name (str): The name of the log

	Returns:
		logging.Logger
	"""

	# If we have no config, setup the reload callback and fetch the data
	if _conf is None:
		config.on_reload(_load_config)
		_load_config()

	# If it's disabled
	if _conf is False:
		return None

	# If the backups isn't an unsigned int
	if not isinstance(_conf['backups'], int) or _conf['backups'] < 0:
		raise ValueError(
			'config.body.logging.backups must be an unsigned integer. '
			f"Received: {str(_conf['backups'])}"
		)

	# If the level is invalid
	if _conf['level'] not in LogLevelMapper:
		raise ValueError(
			'config.body.logging.level must be one of "debug", "critical", '
			'"error", "info", "warning". '
			f"Received: \"{str(_conf['level'])}\""
		)

	# Make sure the path is a string
	if not isinstance(_conf['path'], str):
		raise ValueError(
			'config.body.logging.path must be a string. '
			f"Received: \"{str(_conf['path'])}\""
		)

	# Close it if we already have it
	close_logger(name)

	# Get the folder/directory part versus any prefix of the file
	if _conf['path'].endswith('/'):
		folder, prefix = _conf['path'].rstrip('/') or '/', ''
	else:
		i = _conf['path'].rfind('/')
		if i == -1:
			folder, prefix = '', _conf['path']
		else:
			folder, prefix = _conf['path'][:i] or '/', _conf['path'][i+1:]

	# Check the folder exists
	if folder and not os.path.isdir(folder):
		raise FileNotFoundError(f'{folder} is not a directory')

	# Init the class instances
	instances = {
		'file_handler': None,
		'listener': None,
		'logger': None
	}

	# Init the queue and listener
	_queue = queue.Queue(-1)

	# Get the logger by service name
	instances['logger'] = logging.getLogger(f'service.{name}')
	instances['logger'].setLevel(LogLevelMapper[_conf['level']])
	instances['logger'].propagate = False

	# If it already has the handlers, do nothing
	if instances['logger'].handlers:
		return

	# Create the queue handler and assign it
	instances['logger'].addHandler(
		logging.handlers.QueueHandler(_queue)
	)

	# Create the file handler
	instances['file_handler'] = logging.handlers.TimedRotatingFileHandler(
		filename = f'{folder}/{prefix}{name}.log',
		when = 'midnight',
		interval = 1,
		backupCount = _conf['backups'],
		encoding = 'utf-8'
	)
	instances['file_handler'].setFormatter('')

	# Add the listener for the queue
	instances['listener'] = logging.handlers.QueueListener(
		_queue, instances['file_handler'], respect_handler_level = True
	)
	instances['listener'].start()

	# Add the name to the list of existing
	_loggers[name] = instances

	# Return the actual logger
	return instances['logger']

def _load_config():
	"""Load Config

	Fetches the values from the config
	"""
	global _conf
	_conf = config.body.logging({
		'backups': 30,
		'level': 'info',
		'path': '/var/log/'
	})