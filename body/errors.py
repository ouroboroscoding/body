# coding=utf8
""" Errors

Shared error codes
"""

__author__ = "Chris Nasr"
__copyright__ = "Ouroboros Coding Inc"
__version__ = "1.0.0"
__email__ = "chris@ouroboroscoding.com"
__created__ = "2022-08-29"

# Python imports
from pprint import pformat

# Pip imports
from RestOC import Conf, EMail

RIGHTS = 1000
"""Rights insufficient or missing"""

BODY_FIELD = 1001
"""A specific field in the body is missing or invalid"""

NO_SESSION = 1002
"""No session was passed to the request"""

DB_NO_RECORD = 1100
DB_DUPLICATE = 1101
DB_CREATE_FAILED = 1102
DB_DELETE_FAILED = 1103
DB_UPDATE_FAILED = 1104
DB_KEY_BEING_USED = 1105
DB_ARCHIVED = 1106
"""DB related errors"""

def service_error(error):
	"""Service Error

	Passed to REST instances so we can email errors to developers as soon as
	they happen

	Arguments:
		error (dict): An object with service, path, data, session, environ and
						error message

	Returns:
		bool
	"""

	# If we don't send out errors
	if(not Conf.get(('services', 'send_error_emails'))):
		return True

	# Generate a list of the individual parts of the error
	lErrors = [
		'ERROR MESSAGE\n\n%s\n' % error['traceback'],
		'REQUEST\n\n%s %s:%s\n' % (error['method'], error['service'], error['path']),
		'BODY\n\n%s\n' % pformat(error['body']),
	]
	if 'session' in error and error['session']:
		lErrors.append('SESSION\n\n%s\n' % pformat({k:error['session'][k] for k in error['session']}))
	if 'environ' in error and error['environ']:
		lErrors.append('ENVIRONMENT\n\n%s\n' % pformat(error['environ']))

	# Send the email
	return EMail.error('\n'.join(lErrors))