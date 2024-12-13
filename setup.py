from setuptools import setup

with open('README.md', 'r') as oF:
	long_description=oF.read()

setup(
	name='body-oc',
	version='2.0.1',
	description='Body contains shared concepts among all body parts',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://ouroboroscoding.com/body/',
	project_urls={
		'Documentation': 'https://ouroboroscoding.com/body/',
		'Source': 'https://github.com/ouroboroscoding/body',
		'Tracker': 'https://github.com/ouroboroscoding/body/issues'
	},
	keywords=['rest','microservices'],
	author='Chris Nasr - Ouroboros Coding Inc.',
	author_email='chris@ouroboroscoding.com',
	license='Custom',
	packages=['body'],
	python_requires='>=3.10',
	install_requires=[
		'bottle>=0.12.23,<0.13',
		'gunicorn>=21.2.0,<21.3',
		'jobject>=1.0.2,<1.1.0',
		'jsonb>=1.0.0,<1.1.0',
		'memory-oc>=1.0.0,<1.1',
		'strings-oc>=1.0.7,<1.1',
		'requests>=2.31.0,<2.32',
		'undefined-oc>=1.0.0,<1.1'
	],
	zip_safe=True
)