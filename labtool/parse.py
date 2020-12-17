import re

from dataclasses import dataclass
from operator import attrgetter
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTItem, LTTextBoxHorizontal


POSITION_LEFT   = 0
POSITION_BOTTOM = 1
POSITION_RIGHT  = 2
POSITION_TOP    = 3

LINE_HEIGHT     = 10
ITEM_VPADDING   = 10
ITEM_VTOLERANCY = 5

STANDALONE_FIELDS = [
	'CIP',
	'Data obtenció mostra',
	'Data recepció mostra',
	'Edat',
	'Localització',
	'Metge',
	'NHC',
	'N Laboratori',
	'Observacions',
	'Pacient',
	'Procedència',
	'Servei',
	'Sexe',
	'Unitat de tractament',
]

FIELD_MAPPING = {
	'Pacient': 'Pacient/Nom',
	'NHC': 'Pacient/NHC',
	'CIP': 'Pacient/CIP',
	'Edat': 'Pacient/Edat',
	'Sexe': 'Pacient/Sexe',
	'Servei': 'Pacient/Servei',
	'Unitat de tractament': 'Pacient/Unitat',
	'Localització': 'Pacient/Ubicacio',
	'N Laboratori': 'Peticio/ID',
	'Metge': 'Peticio/Solicitant',
	'Procedència': 'Peticio/Hospital',
	'Observacions': 'Peticio/Observacions',
	'Data obtenció mostra': 'Peticio/Data',
	'Srm-Urea; c.subst.': 'Serum/Urea',
	'Srm-Creatinini; c.subst.': 'Serum/Creatinina',
	'Ren-Filtrat glomerular;cabal vol.(equació CKD-EPI)': 'Renal/Filtrat(CKD-EPI)',
	'Srm-Ió sodi; c.subst.': 'Serum/Sodi',
	'Srm-Ió potassi; c.subst.': 'Serum/Potassi',
	'Srm-Glucosa; c.subst.': 'Serum/Glucosa',
	'Srm-Aspartat-aminotransferasa; c.cat.': 'Serum/AST',
	'Srm-Alanina-aminotransferasa; c.cat.': 'Serum/ALT',
	'Srm-Proteïna; c.massa': 'Serum/Proteina',
	'Srm-gamma-Glutamiltransferasa; c.cat.': 'Serum/GGT',
	'Srm-Fosfatasa alcalina; c.cat.': 'Serum/FA',
	'Srm-Calci(II); c.subst.': 'Serum/Calci',
	'Srm-Factors reumatoides; c.subst.arb.(OMS 64/2)': 'Serum/FR',
	'Srm-Proteïna C reactiva; c.massa': 'Serum/PCR',
	'Srm-Triglicèrid; c.subst.': 'Serum/Triglicerid',
	'Srm-Colesterol; c.subst.': 'Serum/Colesterol',
	'Srm-Colesterol d\'HDL; c.subst.': 'Serum/HDL',
	'Srm-Colesterol d\'LDL; c.subst. (segons Friedewald)': 'Serum/LDL',
	'Srm-Colesterol (exclòs el d\'HDL); c.subst.': 'Serum/No-HDL',
	'Srm-Colesterol d´HDL/Colesterol; quocient subst.': 'Serum/HDL:CT',
	'Srm-Tirotropina; c.subst.arb.': 'Serum/TSH',
	'Srm-Tiroxina(no unida a proteïna); c.subst.': 'Serum/T4L',
	'Hb(San)-Hemoglobina A1c; fr.subst.(expressat en %)': 'Sang/%HbA1c',
	'Hb(San)-Hemoglobina A1c; fr.subst.(IFCC)': 'Sang/HbA1c',
	'Srm-Cobalamines; c.subst.': 'Serum/Cobalamines',
	'Srm-Folats; c.subst.': 'Serum/Folats',
	'Srm-Albúmina; fr.massa': 'Serum/Albumina',
	'Srm-alfa 1-Globulina; fr.massa': 'Serum/A1-Globulina',
	'Srm-alfa 2-Globulina; fr.massa': 'Serum/A2-Globulina',
	'Srm-beta-Globulina; fr.massa': 'Serum/B-Globulina',
	'Srm-gamma-Globulina; fr.massa': 'Serum/G-Globulina',
	'Srm-Anticossos antinuclears i citoplasmàtics; c.arb.': 'Serum/ANAs',
	'Srm-Anticossos anti-DNA doble cadena; c.subst.arb.': 'Serum/Anti-dsDNA',
	'Srm-Ac.(IgG) anticardiolipina(CLIA); c.subst.arb.': 'Serum/Anti-Cardiolipina(IgG)',
	'Srm-Ac.(IgM) anticardiolipina(CLIA); c.subst.arb.': 'Serum/Anti-Cardiolipina(IgM)',
	'Srm-Ac.(IgG) anti-b2-glicoprot(CLIA); c.subst.arb.': 'Serum/Anti-B2GP(IgG)',
	'Srm-Ac.(IgM) anti-b2-glicoprot(CLIA); c.subst.arb.': 'Serum/Anti-B2GP(IgM)',
	'Srm-Ac. antimieloperoxi (MPO)(CLIA); c.subst.arb.': 'Serum/Anti-MPO',
	'Srm-Ac. antiproteïnasa 3(PR3)(CLIA); c.subst.arb.': 'Serum/Anti-PR3',
	'San-Eritròcits; c.nom.': 'Sang/Eritrocits',
	'San-Hemoglobina; c.massa': 'Sang/Hemoglobina',
	'San-Eritròcits; fr.vol.(hematòcrit)': 'Sang/Hematocrit',
	'San-Eritròcits; vol.entític (VCM)': 'Sang/VCM',
	'Ers(San)-Hemoglobina; massa entítica (HCM)': 'Sang/HCM',
	'Ers(San)-Hemoglobina; c.massa (CHCM)': 'Sang/CHCM',
	'Ers(San)-Volum eritrocític; amplada de la distribució rel.': 'Sang/ADE',
	'San-Plaquetes; c.nom.': 'Sang/Plaquetes',
	'San-Plaquetes; vol.entític (VPM)': 'Sang/VPM',
	'San-Leucòcits; c.nom.': 'Sang/Leucocits',
	'San-Neutròfils(segmentats); c.nom.': 'Sang/Neutrofils',
	'San-Limfòcits; c.nom.': 'Sang/Limfocits',
	'San-Monòcits; c.nom.': 'Sang/Monocits',
	'San-Eosinòfils; c.nom.': 'Sang/Eosinofils',
	'San-Basòfils; c.nom.': 'Sang/Basofils',
	'Lks(San)-Neutròfils(segmentats); fr.nom.': 'Sang/%Neutrofils',
	'Lks(San)-Limfòcits; fr.nom.': 'Sang/%Limfocits',
	'Lks(San)-Monòcits; fr.nom.': 'Sang/%Monocits',
	'Lks(San)-Eosinòfils; fr.nom.': 'Sang/%Eosinofils',
	'Lks(San)-Basòfils; fr.nom.': 'Sang/%Basofils',
	'San-Eritrosedimentació; long.': 'Sang/VSG',
	'Pla-Coagulació induïda per factor tissular; temps rel. (temps': 'Plasma/TP',
	'Pla-Coagulació induïda per una superfície; temps rel.(TTPA)': 'Plasma/TTPA',
	'Pla-Fibrinogen; c.massa (coagul.; Clauss)': 'Plasma/Fibrinogen',
	'Pla-Anticoagulant lúpic; c.arb.(negatiu; dubtós; positiu)': 'Plasma/Anticoagulant-Lupic',
}

DUAL_FIELDS = [
	'Serum/Colesterol',
	'Serum/Glucosa',
	'Serum/HDL',
	'Serum/LDL',
	'Serum/No-HDL',
	'Serum/Triglicerid',
]

KNOWN_UNITS = [
	'1',
	'%',
	'mm',
	'pg',
	'U/L', 'ku.i./L', 'mu.int./L',
	'g/L', 'mg/L', 'mg/dL',
	'mmol/L', 'µmol/L', 'pmol/L', 'nmol/L',
	'x10E9/L', 'x10E12/L',
	'mmol/mol',
	'fL',
	'mL/min',
]


@dataclass
class Field:

	name: str

	def __init__(self, name):
		self.name = name
		self._data = []

	def add_data(self, data):
		self._data.append(data)

	def encode(self, encode):
		for fdata in self._data:
			fdata.encode(encode)


@dataclass(frozen=True)
class FieldValue:

	value: str

	def encode(self, encode):
		encode('value', self.value)


@dataclass(frozen=True)
class FieldUnit:

	unit: str

	def encode(self, encode):
		encode('unit', self.unit)


class FieldRefValues:
	pass


@dataclass(frozen=True)
class TwoSidedRefValueInterval(FieldRefValues):

	min: float
	max: float

	def encode(self, encode):
		encode('refvalue.ge', self.min)
		encode('refvalue.lt', self.max)


@dataclass(frozen=True)
class OneSidedRefValueInterval(FieldRefValues):

	GE = '≥'
	GT = '>'
	LE = '≤'
	LT = '<'

	sign: str
	limit: float

	def encode(self, encode):
		if self.sign == self.LT:
			encode('refvalue.lt', self.limit)
		elif self.sign == self.LE:
			encode('refvalue.le', self.limit)
		elif self.sign == self.GT:
			encode('refvalue.gt', self.limit)
		elif self.sign == self.GE:
			encode('refvalue.ge', self.limit)
		else:
			raise NotImplementedError(f'unknown operation {self.sign}')


@dataclass(frozen=True)
class FieldText:

	text: str

	def encode(self, format):
		pass


def normalize_string(s):
	s = re.sub(r'[ \t]+', ' ', s)
	s = s.replace('—', '-')
	return s.strip()


def is_standalone_field(content):
	for m in STANDALONE_FIELDS:
		if content.startswith(f'{m}:'):
			return True
	return False


def parse_standalone_field(content, item):
	key_value = content.split(':')
	if len(key_value) != 2:
		return None

	name = apply_field_mapping(normalize_string(key_value[0]))
	value = normalize_string(key_value[1])

	field = Field(name)
	field.add_data(FieldValue(value=value))
	return field


def is_regular_field(content):

	FIELD_PREFIXES = [
		'San', 'Srm', 'Lks(San)', 'Pla', 'Ers(San)', 'Hb(San)', 'Ren',
	]

	for m in FIELD_PREFIXES:
		if content.startswith(f'{m}-'):
			return True

	return False


def apply_field_mapping(key):
	return FIELD_MAPPING.get(key, key)


def find_field_related_items(limits, available):
	related = []

	left, bottom, _, top = limits
	for (content, pos) in available:
		if pos == limits:
			continue

		ileft, _, _, itop = pos
		if ileft < left:
			continue
		if bottom - itop > ITEM_VTOLERANCY:
			continue
		if itop - top > ITEM_VTOLERANCY:
			continue

		related.append((content, pos))

	return related


def item_ordering(pos):
	fleft, _, _, ftop = pos
	return (-ftop, fleft)


def get_item_content(item):
	return normalize_string(item.get_text())


def try_parse_field_value(content):
	result = re.match(r'(?:\*\s+)?([<>]?\d+(?:\.\d+)?)', content)
	if result is not None:
		return FieldValue(value=result[1])

	if content in ['Pendent', '----']:
		return FieldValue(value=None)

	return None


def try_parse_field_unit(content):
	if content in KNOWN_UNITS:
		return FieldUnit(unit=content)

	return None


def try_parse_field_ref_values(content):
	result = re.match(r'\[ (\d+(?:\.\d+)?) - (\d+(?:\.\d+)?) \]', content)
	if result is not None:
		return TwoSidedRefValueInterval(min=float(result[1]),
		                                max=float(result[2]))

	result = re.match(r'\[ ([<>≤≥]) (\d+(?:\.\d+)?) \]', content)
	if result is not None:
		return OneSidedRefValueInterval(sign=result[1],
		                                limit=float(result[2]))

	return None


def parse_field_related_item(content):
	result = try_parse_field_unit(content)
	if result is not None:
		return result

	result = try_parse_field_value(content)
	if result is not None:
		return result

	result = try_parse_field_ref_values(content)
	if result is not None:
		return result

	return FieldText(text=content)


def parse_fields_while(condition, available):
	fields = []

	for content, _ in available:
		result = parse_field_related_item(content)
		fields.append(result)

		if not condition(result):
			break

	return fields


def parse_field_related_item_set(available):
	assert(available == sorted(available, key=lambda c_p: item_ordering(c_p[1])))

	not_field_value = lambda x: not isinstance(x, FieldValue)
	related  = parse_fields_while(not_field_value, available)
	related += parse_fields_while(not_field_value, available[len(related):])

	if len(related) < len(available):
		related.pop()

	return related


def parse_regular_field(name, limits, available):
	assert(available == sorted(available, key=lambda c_i: item_ordering(c_i[1])))

	field = Field(apply_field_mapping(name))

	related = find_field_related_items(limits, available)
	included = parse_field_related_item_set(related)
	for fdata in included:
		field.add_data(fdata)

	skipped = []
	if field.name in DUAL_FIELDS:
		skipped = parse_field_related_item_set(related[len(included):])

	return field, available[len(included) + len(skipped):]

def parse_lab(f):
	data = {}

	for page in extract_pages(f):
		field_items = []
		value_items = []

		for item in page:
			if not isinstance(item, LTTextBoxHorizontal):
				continue

			text = item.get_text()
			for nline, content in enumerate(text.split('\n')):
				content = normalize_string(content)
				if content == '':
					continue

				position = list(item.bbox)
				position[POSITION_TOP] -= nline * LINE_HEIGHT

				if is_standalone_field(content):
					field = parse_standalone_field(content, item)
					if field is not None and field.name not in data:
						data[field.name] = field
				elif is_regular_field(content):
					field_items.append((content, position))
				else:
					value_items.append((content, position))

		def field_ordering(n_p): return item_ordering(n_p[1])
		field_items = sorted(field_items, key=field_ordering)
		value_items = sorted(value_items, key=field_ordering)

		for i, (name, pos) in enumerate(field_items):
			if i < len(field_items) - 1:
				_, next_pos = field_items[i+1]
				pos[POSITION_BOTTOM] = next_pos[POSITION_TOP] + ITEM_VPADDING

			field, value_items = parse_regular_field(name, pos, value_items)

			if field.name in data:
				continue

			data[field.name] = field

	return data.values()
