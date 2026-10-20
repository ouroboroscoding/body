# coding=utf8
""" Types

Shared types
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2026-10-13"

# Python imports
from typing import Literal

ActionType = Literal[ 'create', 'delete', 'read', 'update' ]
""" The action type """

MethodType = Literal[ 'DELETE', 'GET', 'OPTIONS', 'POST', 'PUT' ]
""" The method type """