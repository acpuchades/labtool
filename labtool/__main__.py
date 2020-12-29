#!/usr/bin/python3

import math, operator, re, sys

from argparse         import ArgumentParser
from dataclasses      import dataclass
from glob             import glob
from numbers          import Number
from operator         import attrgetter

from labtool.parse    import parse_lab
from labtool.encoders import encoders_available, make_encoder


def make_argument_parser():
	parser = ArgumentParser(prog='labtool', description='A tool to analyze compatible lab report files.')
	parser.add_argument('files', nargs='*', help='report files to analyze (PDF)')
	parser.add_argument('-f', '--format', choices=encoders_available(), default='tab', help='output format')
	parser.add_argument('-o', '--output', help='output to file instead of console')
	parser.add_argument('-v', '--verbose', action='store_true', help='show additional info')
	return parser


def make_field_encoder(encoder, field):
	def encode_helper(prop, value):
		return encoder.write_property(field.name, prop, value)

	return encode_helper


def main():
	parser = make_argument_parser()
	args = parser.parse_args()
	out = sys.stdout

	def vprint(message):
		if args.verbose:
			print(message, file=sys.stderr)

	if len(sys.argv) == 1:
		parser.print_help(file=sys.stderr)
		sys.exit()

	if args.output is not None:
		try:
			out = open(args.output, 'w', encoding='utf-8', newline='')
		except IOError as e:
			print(f'Error writing to "{args.output}": {e.strerror}', file=sys.stderr)
			sys.exit(-1)

	try:
		encoder = make_encoder(args, out)
		assert(encoder is not None)
		encoder.begin()

		nrecords = 0
		for pattern in args.files:
			path = None
			for path in glob(pattern):
				vprint(f'Parsing file "{path}"')

				try:
					data = None
					with open(path, 'rb') as f:
						data = parse_lab(f)

					if data is None:
						vprint(f'There was an error trying to parse "{path}", skipping.')
						continue

					encoder.begin_record()
					for field in sorted(data, key=attrgetter('name')):
						field.encode(make_field_encoder(encoder, field))
					encoder.end_record()
					nrecords += 1

				except RuntimeError:
					print(f'There was an error trying to open "{path}", skipping...', file=sys.stderr)

			if not path:
				print(f'No files found matching "{pattern}"', file=sys.stderr)

		encoder.end()

		if args.output is not None:
			if nrecords == 0:
				print(f'No output files were generated', file=sys.stderr)
				sys.exit(-1)

			vprint(f'Writing data to "{args.output}"')

	finally:
		if out is not sys.stdout:
			out.close()


if __name__ == '__main__':
	main()
