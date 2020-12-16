from .csv  import CSVEncoder
from .json import JSONEncoder
from .tab  import TabEncoder


ENCODERS_AVAILABLE = {
	'csv' : CSVEncoder,
	'json': JSONEncoder,
	'tab' : TabEncoder,
}


def make_encoder(args, out):
	Encoder = ENCODERS_AVAILABLE.get(args.format)
	return Encoder(out) if Encoder else None


def encoders_available():
	return ENCODERS_AVAILABLE.keys()