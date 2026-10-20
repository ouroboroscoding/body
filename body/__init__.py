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
	from body.request import Request, RequestException
	from body.response import Error, Response, ResponseException
	from body.service import LogLevel, Service
	from body.rest import REST

__all__ = [
	'create', 'read', 'update', 'delete',
	'Request', 'RequestException',
	'Error', 'Response', 'ResponseException',
	'LogLevel', 'Service',
	'REST'
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

	# request module
	if name == 'Request':
		from body.request import Request
		return Request
	if name == 'RequestException':
		from body.request import RequestException
		return RequestException

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
	if name == 'LogLevel':
		from body.service import LogLevel
		return LogLevel
	if name == 'Service':
		from body.service import Service
		return Service

	# rest module
	if name == 'REST':
		from body.rest import REST
		return REST

	# Nothing found
	raise AttributeError(name)