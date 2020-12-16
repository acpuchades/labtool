import operator

from numbers import Number
from ..      import parse


def make_numeric_checker(opname, limit):
	if opname not in ['lt', 'le', 'gt', 'ge']:
		return None

	op = getattr(operator, opname)

	def numeric_checker(value):
		try:
			n = float(value)
			return op(n, limit)
		except ValueError:
			return True

	return numeric_checker


class TabEncoder:

	FIELD_MAXWIDTH = max(map(len, parse.FIELD_MAPPING.values()))
	VALUE_MAXWIDTH = 12
	UNIT_MAXWIDTH = max(map(len, parse.KNOWN_UNITS))

	def __init__(self, file):
		self._file = file
		self._field = None
		self._value = None
		self._checkers = []

	def begin(self):
		pass

	def begin_record(self):
		self._set_field(None)

	def _set_field(self, field):
		self._field = field
		self._value = None
		self._unit = None
		self._checkers.clear()

	def _output_field(self):
		if self._field == None or self._value == None:
			return

		if all(check(self._value) for check in self._checkers):
			print(' ', end='', file=self._file)
		else:
			print('*', end='', file=self._file)

		print(f' {self._field:{self.FIELD_MAXWIDTH}s}', end='', file=self._file)
		print(f' {self._value:{self.VALUE_MAXWIDTH}s}', end='', file=self._file)
		print(f' {self._unit or "":{self.UNIT_MAXWIDTH}s}', end='', file=self._file)
		print(file=self._file)

	def write_property(self, field, property, value):
		if field != self._field:
			if self._field is not None:
				self._output_field()
			self._set_field(field)

		if property == 'value':
			self._value = value
		elif property == 'unit':
			self._unit = value
		elif property.startswith('refvalue'):
			_, sign = property.split('.')
			checker = make_numeric_checker(sign, value)
			self._checkers.append(checker)

	def end_record(self):
		print(file=self._file)

	def end(self):
		pass
