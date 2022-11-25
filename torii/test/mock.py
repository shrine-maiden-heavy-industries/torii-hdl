# SPDX-License-Identifier: BSD-2-Clause

from ..hdl.rec import Record, DIR_FANIN, DIR_FANOUT

__all__ = (
	'MockRecord',
	'MockPlatform',
)


class MockRecord(Record):
	'''Mock Torii Record

	This class is a modified version of :py:class:`Record`
	that dynamically allocates a record for every field
	requested by name, and caches it.

	This allows :py:class:`MockPlatform` to return an object
	of :py:class:`MockRecord` from ``request`` and have it
	always be "correct".

	This is done by shimming the ``__getitem__`` call and when
	the field lookup fails to allocate a new record with the
	requested name and return that.

	..warning:: This only returns a record with 1-wide ``o`` and ``i`` fields

	'''

	def _insert_field(self, item : str) -> None:
		'''Construct mocked Record

		When the call to ``__getitem__`` runs into a field that
		we have not mocked before, and the field is a str, then
		we insert a mocked record with an ``i`` and ``o`` field
		into the parent records fields.

		..warning:: The field widths are currently set at 1

		Parameters
		----------
		item : str
			The requested field to mock

		'''

		self.fields[item] = Record((
			('o', 1, DIR_FANOUT),
			('i', 1, DIR_FANIN )
		), name = f'{item}')

	def __init__(self, *args, **kwargs) -> None:
		super().__init__((), *args, **kwargs)
		self.fields = {}

	def __getitem__(self, item : str) -> Record:
		'''Return record field

		If the field doesn't exist, we create it with a call
		to ``_insert_field`` then return the generated field.

		Parameters
		----------
		item : Any
			The name of the requested field

		'''

		if isinstance(item, str):
			try:
				return self.fields[item]
			except KeyError:
				self._insert_field(item)
			return self.fields[item]
		else:
			return super().__getitem__(item)

class MockPlatform:
	'''Mock Torii Platform

	This is a mock platform that returns a :py:class:`MockRecord`
	whenever any call to ``request`` is made, regardless of the
	resource being requested.

	'''

	def request(self, name : str, number : int = 0) -> MockRecord:
		'''Request a resource from the platform

		This call returns a :py:class:`MockRecord` regardless
		of any of the parameters passed in.

		Parameters
		----------
		name : str
			The name of the resource to request
		number : int
			The index of the resource to request

		'''

		return MockRecord()
