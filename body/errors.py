# coding=utf8
""" Errors

Shared error codes
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2022-08-29"

REST_REQUEST_DATA = 100
REST_CONTENT_TYPE = 101
REST_AUTHORIZATION = 102
REST_LIST_TO_LONG = 103
REST_LIST_INVALID_URI = 104
"""REST related errors"""

SERVICE_ACTION = 200
SERVICE_STATUS = 201
SERVICE_CONTENT_TYPE = 202
SERVICE_UNREACHABLE = 203
SERVICE_NOT_REGISTERED = 204
SERVICE_NO_SUCH_NOUN = 205
SERVICE_TO_BE_USED_LATER = 206
SERVICE_CRASHED = 207
SERVICE_NO_DATA = 208
SERVICE_NO_SESSION = 209
"""Service related errors"""

RIGHTS = 1000
"""Rights insufficient or missing"""

DATA_FIELDS = 1001
"""One or more data fields is missing or invalid"""

ALREADY_DONE = 1002
"""Indicates the request has already been done, and can't be done again"""

DB_NO_RECORD = 1100
DB_DUPLICATE = 1101
DB_CREATE_FAILED = 1102
DB_DELETE_FAILED = 1103
DB_UPDATE_FAILED = 1104
DB_KEY_BEING_USED = 1105
DB_ARCHIVED = 1106
DB_REFERENCES = 1107
"""DB related errors"""

__all__ = [ n for n,v in globals().items() if isinstance(v, int) ]
""" Export all the constants"""