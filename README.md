# Labtool

A tool to analyze lab report files

# Installing

```console
$ pip install labtool
```

# Usage

```console
$ labtool --help

usage: labtool [-h] [-f {csv,json,tab}] [-o OUTPUT] [-v] [files ...]

A tool to analyze compatible lab report files.

positional arguments:
  files                 report files to analyze (PDF)

optional arguments:
  -h, --help            show this help message and exit
  -f {csv,json,tab}, --format {csv,json,tab}
                        output format
  -o OUTPUT, --output OUTPUT
                        output to file instead of console
  -v, --verbose         show additional info
```