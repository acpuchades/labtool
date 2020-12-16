import csv


class CSVEncoder:

	def __init__(self, file):
		self._file = file
		self._rows = []
		self._colnames = set()
		self._current_row = None

	def begin(self):
		self._rows.clear()
		self._colnames.clear()
		self._current_row = None

	def begin_record(self):
		self._current_row = {}

	def write_property(self, field, property, value):
		if property != 'value':
			return

		self._colnames.add(field)
		self._current_row[field] = value

	def end_record(self):
		self._rows.append(self._current_row)
		self._current_row = None

	def end(self):
		writer = csv.DictWriter(self._file, sorted(self._colnames))
		writer.writeheader()
		writer.writerows(self._rows)
