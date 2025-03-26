# coding=utf8
""" Parser

Parses a method's docstring to get all the parts
"""

__author__		= "Chris Nasr"
__version__		= "1.0.0"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2025-02-23"

# Python imports
import re

# Regular expressions
_google_section = re.compile(r'^([^\s:]+(?: [^\s:]+)*):\s*(.*)$')
_google_whitespace = re.compile(r'^(\s+)')

def parse_google(s: str) -> dict:
	"""Google

	Parsers google style docstring and returns the sections found

	Arguments:
		s (str): The docstring to parse

	Returns:
		dict
	"""

	# Split the docstring into lines
	lLines = s.split('\n')

	# Init the return with the name
	dSections = {
		'name': lLines[0].strip(),
		'description': []
	}

	# Start with the description
	sKey = 'description'

	# Init the whitespace regex
	oWhitespace = None

	# Loop through the remaining lines
	for sLine in lLines[1:]:

		# If the line is a new section header
		m = _google_section.match(sLine)
		if m:

			# If we need to skip it
			if sLine[0] == '-' and sLine[-1] == '-':
				sLine = sLine[1:-1]

			# Else, continue processing the new section
			else:

				# Check the last line of the previous section, if it's an empty line
				#	delete it
				if len(dSections[sKey]) and dSections[sKey][-1].strip() == '':
					dSections[sKey].pop()

				# If the previous section is empty
				if not dSections[sKey]:
					del dSections[sKey]

				# Clear the whitespace
				oWhitespace = None

				# Store the new section name
				sKey = m.group(1).lower().replace(' ', '_')
				dSections[sKey] = []

				# If we have a group 2, set it as the new line
				if m.group(2) is not None:
					sLine = m.group(2)

				# Else, loop back around to the next line
				else:
					continue

		# If we have nothing in the section yet
		if not dSections[sKey]:

			# If the line is empty, skip it
			if sLine.strip() == '':
				continue

			# If the line has whitespace
			m = _google_whitespace.match(sLine)
			if m:
				oWhitespace = re.compile('^(?:%s)?(.*)' % m.group(1))

		# If we have whitespace
		if oWhitespace:

			# Strip it off
			m = oWhitespace.match(sLine)
			sLine = m.group(1)

		# Add the line to the current section
		dSections[sKey].append(sLine)

	# Check the last section
	if not dSections[sKey]:
		del dSections[sKey]

	# Go through each section and turn lines into a string
	for s in dSections:
		if isinstance(dSections[s], list):
			dSections[s] = '\n'.join(dSections[s])

	# Return the sections
	return dSections