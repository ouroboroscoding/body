# coding=utf8
"""Body

Shared methods for accessing the brain and other shared formats
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2022-08-29"

__all__ = [
	'create', 'read', 'update', 'delete',
	'Service', 'Error', 'Response', 'ResponseException'
]

# Import external calls and Service
from body.external import create, delete, read, update
from body.response import Error, Response, ResponseException
from body.service import Service