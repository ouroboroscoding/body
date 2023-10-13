# coding=utf8
""" Service

Holds the class used to create services that can be started as rest apps
"""

__author__		= "Chris Nasr"
__copyright__	= "Ouroboros Coding Inc."
__email__		= "chris@ouroboroscoding.com"
__created__		= "2023-03-15"

# Python imports
import abc

class Service(abc.ABC):
	"""Service

	The object to build all services from
	"""

	@abc.abstractmethod
	def reset(self):
		"""Reset

		Called when the system has been reset, usually by loading new data that
		the instance will need to process/reprocess

		Returns:
			None
		"""
		raise NotImplementedError('Must implement the "reset" method')