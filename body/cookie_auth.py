# coding=utf8
"""Auth(orization) Cookie

Allows setting, getting, and clearing the cookie associated with authorization
"""
from __future__ import annotations

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2026-10-21"

__all__ = [ 'clear', 'name', 'set' ]

# Ouroboros imports
import config
import undefined

# Pip imports
import bottle

# Local imports
from body.constants import SECONDS_365_DAYS

# Local variable
_name = undefined
def _load_name():
	global _name
	val = config.body.rest.cookie(False)
	if isinstance(val, bool):
		if val: val = 'session'
		_name = val
	elif isinstance(val, str) and val:
		_name = val
	else:
		raise ValueError(
			f'{str(val)} ({type(val).__name__}) is not a valid '
			'config.body.rest.cookie value'
		)

# Load / reload cookie name
config.on_reload(_load_name)
_load_name()

def clear():
	"""Clear

	Deletes the cookie for the session
	"""

	# If we have no cookie
	if _name is False:
		return

	# Delete the cookie
	bottle.response.set_cookie(
		_name,
		'',
		max_age = 0,
		path = '/',
		secure = True,
		samesite = 'Lax',
		httponly = True
	)

def get():
	"""Get

	Gets the value of the cookie if we have cookies enabled and the value
	exists

	Returns:
		str | None
	"""

	# If we have no cookie
	if _name is False:
		return None

	# Return the value
	return bottle.request.cookies.get(_name, None)

def name():
	"""Name

	Gets the name of the cookie, else None

	Returns:
		str | None
	"""
	return _name

def set(key, ttl):
	"""Set

	Sets the httpOnly cookie for the session

	Arguments:
		key (str): The session key
		ttl (uint): The time to live for the cookie
	"""

	# If we have no cookie
	if _name is False:
		return

	# If the ttl is 0
	iTTL = ttl or SECONDS_365_DAYS

	# Set the cookie in bottle
	bottle.response.set_cookie(
		_name,
		key,
		max_age = iTTL,
		path = '/',
		secure = True,
		samesite = 'Lax',
		httponly = True
	)