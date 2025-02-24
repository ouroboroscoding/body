# coding=utf8
""" Body Docs

Main entry into calling the rest documentation generator
"""

__author__		= "Chris Nasr"
__version__		= "1.0.0"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2025-02-23"

# Python imports
from argparse import ArgumentParser
from sys import exit, stderr

# Constants
EXTENSIONS = { 'markdown': 'md' }

# Local impors
from . import handle_file, generate_service

def cli() -> int:
	"""CLI

	Handles generating a service's documentation via the command line interface

	Returns:
		int
	"""

	# Setup the argument parser
	oArgParser = ArgumentParser(
		description='Body - Generate REST Documentation'
	)
	oArgParser.add_argument(
		'-f', '--format', nargs=1, default='markdown',
		help='The format to out the documentation in. Only supports ' \
			'"markdown" at present'
	)
	oArgParser.add_argument(
		'-o', '--output', default='./',
		help='The folder to store generated documentation in'
	)
	oArgParser.add_argument(
		'-p', '--parser', nargs=1, default='google',
		help='The parser to use for docstrings. Only supports "google" at ' \
			'present'
	)
	oArgParser.add_argument(
		'file', nargs="+",
		help='The file(s) to parse and generate documentation from'
	)
	oArgs = oArgParser.parse_args()

	# If the format is anything other than markdown
	if oArgs.format != 'markdown':
		print('Invalid option for --format: "%s"' % oArgs.format,
			file = stderr)
		print('body-docs only supports "markdown" generator')
		return 0

	# If the parser is anything other than markdown
	if oArgs.parser != 'google':
		print('Invalid option for --parser: "%s"' % oArgs.format,
			file = stderr)
		print('body-docs only supports "google" docstring format')
		return 0

	# Init the list of services
	lServices = []

	# Go through each file passed
	for sFile in oArgs.file:

		# Handle the file
		mRes = handle_file(sFile, oArgs.parser)
		if not mRes:
			print('Failed to handle file "%s"' % sFile, file = stderr)
			return 1

		# Extend the list
		lServices.extend(mRes)

	# If we have services
	if lServices:

		# Generate a file for each
		for dService in lServices:
			print('Generating "%s"' % dService['name'])
			if not generate_service(
				dService,
				oArgs.format,
				oArgs.output.rstrip('/')
			):
				print('Failed to generate "%s"' % dService['name'],
		  			file = stderr)
				return 1

	# Return OK
	return 0

# Only run if called directly
if __name__ == '__main__':
	exit(cli())