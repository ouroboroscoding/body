# coding=utf8
""" Types

Shared types
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2026-10-13"

# Python imports
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from typing import Literal

ActionType = Literal[ 'create', 'delete', 'read', 'update' ]
""" The action type """

LogLevelType = Literal[ 'critical', 'debug', 'error', 'info', 'warning' ]
""" The log level type """

LogLevelMapper = {
	'critical': CRITICAL,
	'debug': DEBUG,
	'error': ERROR,
	'info': INFO,
	'warning': WARNING
}
""" Maps log level type to the actual logging module constant"""