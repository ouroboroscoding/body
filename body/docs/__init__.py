# coding=utf8
""" Docs

Generates markdown file of all request points in a service
"""

__author__		= "Chris Nasr"
__version__		= "1.0.0"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2025-02-23"

# Ouroboros imports
from strings import to_file

# Python imports
import ast
from os import path
import re
from sys import exit, stderr
from typing import List, Literal

# Local imports
from .parser import parse_google

# Regular expressions
_service = re.compile(r'request:\s*(\w+)', re.IGNORECASE)
_data = re.compile(
	r'^([^,]+)\s*,\s*([^,]+)\s*,\s*(no|yes)\s*,\s*(.+)$', re.IGNORECASE
)
_error = re.compile(r'^(\d+)\s*,\s*((?:[a-z0-9_]+\.)?[A-Z0-9_]+)\s*,\s*(.+)$')
_response = re.compile(r'^([^,]+)\s*,\s*([^,]+)\s*,\s*(.+)$')

# Constants
EXTENSIONS = { 'markdown': 'md' }

def handle_class(
	_class: ast.ClassDef,
	parser: Literal['google']
) -> dict | Literal[False]:
	"""Handle Class

	Looks through a Service class and generates the data for the documentation

	Arguments:
		_class (ast.ClassDef): The AST definition of the class we will step
			through
		parser ('google'): The parser to use for the docstrings

	Returns:
		dict | False
	"""

	# If it's not a Service class
	if not any([ o.id == 'Service' for o in _class.bases ]):
		return False

	# Init the return
	dRet = {
		'name': _class.name,
		'file': _class.name.lower(),
		'uri': _class.name.lower(),
		'requests': [ ]
	}

	# Get the docstring and store it
	sDoc = ast.get_docstring(_class, True)

	# Parse the docstring to get the sections
	if parser == 'google':
		dSections = parse_google(sDoc)
	else:
		raise ValueError('parser', 'invalid parser "%s"' % parser)

	# If we have a name override
	if 'docs-file' in dSections:
		dRet['file'] = dSections['docs-file']
	elif 'docs_file' in dSections:
		dRet['file'] = dSections['docs_file']

	# Add the description
	dRet['description'] = dSections['description']

	# If we have a body overwrite
	if 'docs-body' in dSections:
		dRet['body'] = dSections['docs-body']
	elif 'docs_body' in dSections:
		dRet['body'] = dSections['docs_body']

	# Step through each child of the class
	for oMethod in _class.body:

		# If it's not a function
		if not isinstance(oMethod, ast.FunctionDef):
			continue

		# Handle the method
		mRes = handle_method(oMethod, parser)
		if mRes:
			dRet['requests'].append(mRes)

	# Return OK
	return dRet

def handle_file(
	file: str,
	parser: Literal['google']
) -> List[dict] | Literal[False]:
	"""Handle File

	Looks through a single file for Service classes. Returns False is anything
	fails, else a list of services found in the file

	Arguments:
		file (str): The path to the file
		parser ('google'): The parser to use for the docstrings

	Returns:
		dict[] | False
	"""

	# If the file does not exist
	if not path.exists(file):
		print('File "%s" does not exist' % file, file = stderr)
		return False

	# Open the file
	with open(file) as oF:

		# Get the abstract syntax tree for the file
		try:
			oAST = ast.parse(oF.read(), file)

			# Init list of services
			lServices = []

			# Go through each node in the tree
			for oClass in ast.iter_child_nodes(oAST):

				# If it's a class
				if isinstance(oClass, ast.ClassDef):

					# Handle the class
					mRes = handle_class(oClass, parser)
					if mRes:
						lServices.append(mRes)

			# If there's no services
			if not lServices:
				return False

			# Return OK
			return lServices

		# Catch syntax errors from broken code
		except SyntaxError as e:
			print('Syntax Error parsing "%s" at line %d, column %d\n' % (
				file,
				e.args[1][1],
				e.args[1][2]
			), file = stderr)
			return False

	# Strange
	print('Unknown issue reading "%s"' % file, file = stderr)
	return False

def handle_method(
	method: ast.FunctionDef,
	parser: Literal['google']
) -> dict | Literal[False]:
	"""Handle Method

	Looks through a service method and generates the data for the documentation

	Arguments:
	 	method (ast.FunctionDef): The AST definition of the method
		parser ('google'): The parser to use for the docstrings

	Returns:
		dict | False
	"""

	# Split the name and store the parts
	lParts = method.name.split('_')

	# If it's not a valid action
	if lParts[-1] not in [ 'create', 'delete', 'read', 'update' ]:
		return False

	# If it doesn't have the expected arguments
	try:
		lArgs = [ o.arg for o in method.args.args ]
		if lArgs != [ 'self', 'req' ]:
			return False
	except Exception:
		return False

	# Init the return
	dRet = {
		'action': lParts[-1],
		'noun': ' '.join(lParts[:-1]),
		'uri': '/'.join(lParts[:-1])
	}

	# Get the docstring and store it
	sDoc = ast.get_docstring(method, True)

	# Parse the docstring to get the sections
	if parser == 'google':
		dSections = parse_google(sDoc)
	else:
		raise ValueError('parser', 'invalid parser "%s"' % parser)

	# Add the name and description
	dRet['name'] = dSections['name']
	dRet['description'] = 'description' in dSections and \
		dSections['description'] or ''

	# If we have a data section
	if 'data' in dSections:

		# Split data into lines, strip whitespace
		lLines = [ s.strip() for s in dSections['data'].split('\n') ]

		# Init data
		lData = []

		# Go through each line
		for s in lLines:

			# Match it
			m = _data.match(s)
			if not m:
				print('Invalid "data" line in "%s" docstring: %s' % (
					method.name, s
				), file = stderr)
			else:
				lData.append({
					'name': m.group(1),
					'type': m.group(2),
					'optional': m.group(3),
					'descr': m.group(4)
				})

		# If we have any, add it
		if lData:
			dRet['data'] = lData

		# Else, just pass the original string
		else:
			dRet['data'] = dSections['data']

	# If we have a response section
	if 'response' in dSections:

		# Split response into lines, strip whitespace
		lLines = [ s.strip() for s in dSections['response'].split('\n') ]

		# Init response
		lResponse = []

		# Go through each line
		for s in lLines:

			# Match it
			m = _response.match(s)
			if m:
				lResponse.append({
					'name': m.group(1),
					'type': m.group(2),
					'descr': m.group(3)
				})

		# If we have any, add it
		if lResponse:
			dRet['response'] = lResponse

		# Else, just pass the original string
		else:
			dRet['response'] = dSections['response']

	# If we have a response example
	if 'response_example' in dSections:
		dRet['response_example'] = dSections['response_example']

	# If we have an error section
	if 'error' in dSections:

		# Split error into lines, strip whitespace
		lLines = [ s.strip() for s in dSections['error'].split('\n') ]

		# Init error
		lError = []

		# Go through each line
		for s in lLines:

			# Match it
			m = _error.match(s)
			if not m:
				print('Invalid "error" line in "%s" docstring: %s' % (
					method.name, s
				), file = stderr)
			else:
				lError.append({
					'code': m.group(1),
					'const': m.group(2),
					'descr': m.group(3)
				})

		# If we have any, add it
		if lError:
			dRet['error'] = lError

	# If we have an example section
	if 'example' in dSections:
		dRet['example_raw'] = dSections['example']
	elif 'data_example' in dSections:
		dRet['data_example'] = dSections['data_example']

	# Return the info
	return dRet

def generate_service(service: dict, format: str, output: str):
	"""Generate Service

	Generates a single file with all documentation for the service

	Arguments:
		service (dict): The service info with the nouns
		format ('markdown'): The format used to generate the docs
		output (str): The directory to store the docs in
	"""

	# Load and init Jinja2
	try:
		from jinja2 import Environment, PackageLoader, select_autoescape
		oJinja = Environment(
			autoescape = select_autoescape(),
			loader = PackageLoader('body.docs'),
			lstrip_blocks = True,
			trim_blocks = True
		)

	# Notify the user to install Jinja2 in development
	except ModuleNotFoundError as e:
		print('Using "body-docs" requires that Jinja2 be installed. It is ' \
			'not installed by default to save space on production installs.\n' \
			'To install jinja2 run the following in your venv:\n\n' \
			'pip install jinja2', file = stderr)
		exit(1)

	# Get the template based on the format
	oTpl = oJinja.get_template('%s.j2' % format)

	# Render the template and save it to the output folder
	return to_file(
		'%s/%s.%s' % ( output, service['file'], EXTENSIONS[format] ),
		oTpl.render(**service)
	)