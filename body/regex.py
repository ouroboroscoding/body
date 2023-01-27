# coding=utf8
""" Regex

Shared regular expressions
"""

__author__ = "Chris Nasr"
__copyright__ = "Ouroboros Coding Inc"
__version__ = "1.0.0"
__email__ = "chris@ouroboroscoding.com"
__created__ = "2023-01-25"

# Python imports
import re

EMAIL_ADDRESS = re.compile(r'[^@\s]+@[^@\s]+\.[a-zA-Z0-9]{2,}$')
"""Email Address"""

PHONE_NUMBER_NA = re.compile(r'\+?1?[ -]?\(?(\d{3})\)?[ -]?(\d{3})[ -]?(\d{4})')
"""North American Phone Number"""