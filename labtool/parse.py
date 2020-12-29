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
	'Data obtencio mostra',
	'Data recepcio mostra',
	'Edat',
	'Localitzacio',
	'Metge',
	'N Laboratori',
	'NHC',
	'Observacions',
	'Pacient',
	'Procedencia',
	'Servei',
	'Sexe',
	'Unitat de tractament',
]

FIELD_MAPPING = {

	# Standalone Fields

	'CIP': 'Pacient/CIP',
	'Data obtencio mostra': 'Peticio/Data',
	'Edat': 'Pacient/Edat',
	'Localitzacio': 'Pacient/Ubicacio',
	'Metge': 'Peticio/Solicitant',
	'N Laboratori': 'Peticio/ID',
	'NHC': 'Pacient/NHC',
	'Observacions': 'Peticio/Observacions',
	'Pacient': 'Pacient/Nom',
	'Procedencia': 'Peticio/Hospital',
	'Servei': 'Pacient/Servei',
	'Sexe': 'Pacient/Sexe',
	'Unitat de tractament': 'Pacient/Unitat',

	# Regular fields

	'Ers(San)-Hemoglobina;c.massa(CHCM)': 'Sang/CHCM',
	'Ers(San)-Hemoglobina;massa entitica(HCM)': 'Sang/HCM',
	'Ers(San)-Reticulocits;fr.nom.': 'Sang/%Reticulocits',
	'Ers(San)-Volum eritrocitic;amplada de la distribucio rel.': 'Sang/ADE',
	'Gas(vSan)-Dioxid de carboni;pr.parc.': 'Sang(v)/pCO2',
	'Gas(vSan)-Oxigen;pr.parc.': 'Sang(v)/pO2',
	'Hb(San)-Hemoglobina A1c;fr.subst.(IFCC)': 'Sang/HbA1c',
	'Hb(San)-Hemoglobina A1c;fr.subst.(expressat en %)': 'Sang/%HbA1c',
	'Hb(vSan)-Oxigen;fr.sat.': 'Sang(v)/%SatHb',
	'Lks(San)-Basofils;fr.nom.': 'Sang/%Basofils',
	'Lks(San)-Eosinofils;fr.nom.': 'Sang/%Eosinofils',
	'Lks(San)-Limfocits;fr.nom.': 'Sang/%Limfocits',
	'Lks(San)-Metamielotics;fr.nom': 'Sang/%Metamielocits',
	'Lks(San)-Monocits;fr.nom.': 'Sang/%Monocits',
	'Lks(San)-Neutrofils(segmentats);fr.nom.': 'Sang/%Neutrofils',
	'Pac(vSan)-Plasma;pH': 'Sang(v)/pH',
	'Pla-Alanina-aminotransferasa;c.cat.': 'Serum/ALT',
	'Pla-Anticoagulant lupic;c.arb.(negatiu;dubtos;positiu)': 'Plasma/Anticoagulant-Lupic',
	'Pla-Aspartat-aminotransferasa;c.cat.': 'Serum/AST',
	'Pla-Bilirubina;c.subst.': 'Serum/Bilirrubina',
	'Pla-Calci(II);c.subst.': 'Serum/Calci',
	'Pla-Clorur;c.subst.': 'Serum/Clorur',
	'Pla-Coagulacio induida per factor tissular;INR(temps de': 'Plasma/INR',
	'Pla-Coagulacio induida per factor tissular;INR(temps': 'Plasma/INR',
	'Pla-Coagulacio induida per factor tissular;temps rel.(temps': 'Plasma/TP',
	'Pla-Coagulacio induida per una superficie;temps rel.(TTPA)': 'Plasma/TTPA',
	'Pla-Creatina-cinasa;c.cat.': 'Serum/CK',
	'Pla-Creatinini;c.subst.': 'Serum/Creatinina',
	'Pla-Fibrinogen(coag);c.massa': 'Plasma/Fibrinogen',
	'Pla-Fibrinogen;c.massa(coagul.;Clauss)': 'Plasma/Fibrinogen',
	'Pla-Fibrinogen;c.massa(coagul.;derivat)': 'Plasma/Fibrinogen',
	'Pla-Glucosa;c.subst.': 'Sang/Glucosa',
	'Pla-Io calci;c.subst.(pH 7.4)': 'Serum/Calci(ionitzat)',
	'Pla-Io potassi;c.subst.': 'Serum/Potassi',
	'Pla-Io sodi;c.subst.': 'Serum/Sodi',
	'Pla-Lactat;c.subst.': 'Serum/Lactat',
	'Pla-Proteina C reactiva;c.massa(CRM 470)': 'Serum/PCR',
	'Pla-Proteina;c.massa': 'Serum/Proteines',
	'Pla-Troponina T;c.massa': 'Serum/TnT',
	'Pla-Urea;c.subst.': 'Sang/Urea',
	'Pla-alfa-Amilasa;c.cat.': 'Serum/Amilasa',
	'Ren-Filtrat glomerular;cabal vol.(equacio CKD-EPI)': 'Renal/Filtrat(CKD-EPI)',
	'San-Basofils;c.nom.': 'Sang/Basofils',
	'San-Eosinofils;c.nom.': 'Sang/Eosinofils',
	'San-Eritrocits;c.nom.': 'Sang/Eritrocits',
	'San-Eritrocits;fr.vol.(hematocrit)': 'Sang/Hematocrit',
	'San-Eritrocits;v.entitic(VCM)': 'Sang/VCM',
	'San-Eritrocits;vol.entitic(VCM)': 'Sang/VCM',
	'San-Eritrosedimentacio;long.': 'Sang/VSG',
	'San-Hemoglobina;c.massa': 'Sang/Hemoglobina',
	'San-Leucocits;c.nom.': 'Sang/Leucocits',
	'San-Limfocits T CD4;c.nom.': 'Sang/CD4',
	'San-Limfocits;c.nom.': 'Sang/Limfocits',
	'San-Monocits;c.nom.': 'Sang/Monocits',
	'San-Neutrofils(segmentats);c.nom.': 'Sang/Neutrofils',
	'San-Plaquetes;c.nom.': 'Sang/Plaquetes',
	'San-Plaquetes;vol.entitic(VPM)': 'Sang/VPM',
	'San-Reticulocits;c.nom.': 'Sang/Recitulocits',
	'Srm-Ac.(IgG)anti-b2-glicoprot(CLIA);c.subst.arb.': 'Serum/Anti-B2GP(IgG)',
	'Srm-Ac.(IgG)anticardiolipina(CLIA);c.subst.arb.': 'Serum/Anti-Cardiolipina(IgG)',
	'Srm-Ac.(IgM)anti-b2-glicoprot(CLIA);c.subst.arb.': 'Serum/Anti-B2GP(IgM)',
	'Srm-Ac.(IgM)anticardiolipina(CLIA);c.subst.arb.': 'Serum/Anti-Cardiolipina(IgM)',
	'Srm-Ac.antimieloperoxi(MPO)(CLIA);c.subst.arb.': 'Serum/Anti-MPO',
	'Srm-Ac.antiproteinasa 3(PR3)(CLIA);c.subst.arb.': 'Serum/Anti-PR3',
	'Srm-Alanina-aminotransferasa;c.cat.': 'Serum/ALT',
	'Srm-Albumina;c.massa(CRM 470)': 'Serum/Albumina',
	'Srm-Albumina;fr.massa': 'Serum/Albumina',
	'Srm-Anticossos anti-DNA doble cadena;c.subst.arb.': 'Serum/Anti-dsDNA',
	'Srm-Anticossos antimieloperoxidasa(MPO)(CLIA);': 'Serum/Anti-MPO',
	'Srm-Anticossos antinuclears i citoplasmatics;c.arb.': 'Serum/ANAs',
	'Srm-Anticossos(IgG)anticardiolipina(CLIA);c.subst.arb.': 'Serum/Anti-Cardiolipina(IgG)',
	'Srm-Anticossos(IgM)anticardiolipina(CLIA);c.subst.arb.': 'Serum/Anti-Cardiolipina(IgG)',
	'Srm-Aspartat-aminotransferasa;c.cat.': 'Serum/AST',
	'Srm-Bilirubina;c.subst.': 'Serum/Bilirrubina',
	'Srm-Calci(II);c.subst.': 'Serum/Calci',
	'Srm-Clorur;c.subst.': 'Serum/Clorur',
	'Srm-Cobalamines;c.subst.': 'Serum/Cobalamines',
	'Srm-Colesterol d\'HDL/Colesterol;quocient subst.': 'Serum/HDL:CT',
	'Srm-Colesterol d\'HDL;c.subst.': 'Serum/HDL',
	'Srm-Colesterol d\'LDL;c.subst.(segons Friedewald)': 'Serum/LDL',
	'Srm-Colesterol(exclos el d\'HDL);c.subst.': 'Serum/No-HDL',
	'Srm-Colesterol;c.subst.': 'Serum/Colesterol',
	'Srm-Component monoclonal;c.massa': 'Serum/Component-Monoclonal',
	'Srm-Creatinini;c.subst.': 'Serum/Creatinina',
	'Srm-Factors reumatoides;c.subst.arb.(OMS 64/2)': 'Serum/FR',
	'Srm-Folats;c.subst.': 'Serum/Folats',
	'Srm-Fosfat;c.subst.': 'Serum/Fosfat',
	'Srm-Fosfatasa alcalina;c.cat.': 'Serum/FA',
	'Srm-Glucosa;c.subst.': 'Serum/Glucosa',
	'Srm-Glucosa;c.subst.(mitjana estimada)': 'Serum/Glucosa',
	'Srm-Io potassi;c.subst.': 'Serum/Potassi',
	'Srm-Io sodi;c.subst.': 'Serum/Sodi',
	'Srm-Magnesi(II);c.subst.': 'Serum/Magnesi',
	'Srm-Prealbumina(transtiretina);c.massa': 'Serum/Prealbumina',
	'Srm-Proteina C reactiva;c.massa': 'Serum/PCR',
	'Srm-Proteina C reactiva;c.massa(CRM 470)': 'Serum/PCR',
	'Srm-Proteina;c.massa': 'Serum/Proteina',
	'Srm-Tirotropina;c.subst.arb.': 'Serum/TSH',
	'Srm-Tiroxina(no unida a proteina);c.subst.': 'Serum/T4L',
	'Srm-Triglicerid;c.subst.': 'Serum/Triglicerid',
	'Srm-Urat;c.subst.': 'Serum/Urat',
	'Srm-Urea;c.subst.': 'Serum/Urea',
	'Srm-alfa 1-Globulina;fr.massa': 'Serum/A1-Globulina',
	'Srm-alfa 2-Globulina;fr.massa': 'Serum/A2-Globulina',
	'Srm-beta-Globulina;fr.massa': 'Serum/B-Globulina',
	'Srm-gamma-Globulina;fr.massa': 'Serum/G-Globulina',
	'Srm-gamma-Glutamiltransferasa;c.cat.': 'Serum/GGT',
	'vPla-Exces de base(llocs enllaçants d\'H+);c.subst.': 'Sang(v)/EB',
	'vPla-Hidrogencarbonat;c.subst': 'Sang(v)/Bicarbonat',

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
	'%',
	'1',
	'CU',
	'U/L',
	'fL',
	'g/L',
	'karb.u./L',
	'kint.u./L',
	'ku.i./L',
	'mL/min',
	'mg/L',
	'mg/dL',
	'mm',
	'mmHg',
	'mmol/L',
	'mmol/mol',
	'mu.int./L',
	'nmol/L',
	'pg',
	'pmol/L',
	'ukat/L',
	'umol/L',
	'x10E12/L',
	'x10E9/L',
	'µmol/L',
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

	# Coalesce whitespace
	s = re.sub(r'[ \t]+', ' ', s)

	# Fix inconsistent whitespace
	s = re.sub(r' ([;\(])', r'\1', s)
	s = re.sub(r'([.;\)]) ', r'\1', s)

	# Fix inconsistent quoting
	s = re.sub(r'([-;\(\)])[\'"]', r'\1', s)
	s = re.sub(r'[\'"]([-;\(\)])', r'\1', s)

	# Replace unicode characters with ASCII equivalents
	s = s.replace('—', '-')
	s = s.replace('à', 'a')
	s = s.replace('ú', 'u')
	s = re.sub('[`´]', "'", s)
	s = re.sub('[èé]', 'e', s)
	s = re.sub('[íï]', 'i', s)
	s = re.sub('[òó]', 'o', s)

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
		'Ers(San)',
		'Gas(vSan)',
		'Hb(San)',
		'Hb(vSan)',
		'Lks(San)',
		'Pac(vSan)',
		'Pla',
		'Ren',
		'San',
		'Srm',
		'vPla',
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

	result = re.match(r'(?:Valor|Concentracio) desitjable ([<>≤≥]) (\d+(?:\.\d+)?)', content)
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

		field_ordering = lambda n_p: item_ordering(n_p[1])
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
