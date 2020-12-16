import json


class JSONEncoder:

	def __init__(self, file):
		self._file = file
		self._rows = []
		self._current_row = None

	def begin(self):
		self._records = []

	def begin_record(self):
		self._data = {}

	def write_property(self, field, property, value):
		if property != 'value':
			return

		parent = self._data
		*scopes, name = field.split('/')
		for s in scopes:
			parent = parent.setdefault(s, {})
		parent[name] = value

	def end_record(self):
		self._records.append(self._data)
		self._data = {}

	def end(self):
		import json

		json.dump(self._records, self._file, sort_keys=True, indent=2)
