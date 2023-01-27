# coding=utf8
""" Users

Shared methods for accessing user info
"""

__author__ = "Chris Nasr"
__copyright__ = "Ouroboros Coding Inc"
__version__ = "1.0.0"
__email__ = "chris@ouroboroscoding.com"
__created__ = "2022-08-29"

# Pip imports
from RestOC import Services

SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000000'
"""System User ID"""

def details(_id, fields=None, order=None, as_dict='_id'):
	"""Details

	Fetches user info from IDs

	Arguments:
		_id (str|str[]) The ID(s) to fetch info for
		fields (str[]): The list of fields to return
		order (str[]): The list of fields to order by
		as_dict (bool): Optional, if not set/true, returns a list, if set, must
						be a field that's passed

	Returns:
		dict|list
	"""

	# Init the data by adding the ID(s) and the internal key
	dData = {
		'_internal_': Services.internal_key(),
		'_id': _id
	}

	# If we want specific fields
	if fields:
		dData['fields'] = fields

	# If we want a specific order
	if order:
		dData['order'] = order

	# Make the request using an internal key
	oResponse = Services.request('brain', 'read', 'users', dData)

	# If there's an error
	if oResponse.error_exists():

		# Throw it
		raise Services.ResponseException(oResponse)

	# If we don't want a dict
	if not as_dict:
		return oResponse.data

	# Convert the data into a dictionary
	dUsers = {}
	for d in oResponse.data:

		# Pop off the field used as a key
		sKey = d.pop(as_dict)

		# Store the rest by the key
		dUsers[sKey] = d

	# Return the users
	return dUsers
