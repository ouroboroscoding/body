# coding=utf8
"""Body

Shared methods for accessing the brain and other shared formats
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2022-08-29"

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from body.external import create, delete, read, update
	from body.response import Error, Response, ResponseException
	from body.service import Service

__all__ = [
	'create', 'read', 'update', 'delete',
	'Service', 'Error', 'Response', 'ResponseException'
]

def __dir__():
	return sorted(set(globals()) | set(__all__))

def __getattr__(name):

	# external module
	if name == 'create':
		from body.external import create
		return create
	if name == 'delete':
		from body.external import delete
		return delete
	if name == 'read':
		from body.external import read
		return read
	if name == 'update':
		from body.external import update
		return update

	# response module
	if name == 'Error':
		from body.response import Error
		return Error
	if name == 'Response':
		from body.response import Response
		return Response
	if name == 'ResponseException':
		from body.response import ResponseException
		return ResponseException

	# service module
	if name == 'Service':
		from body.service import Service
		return Service