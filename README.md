# parse-file-challenge
Parse a CSV File for Python Code Challenge
A Python command line app that retrieves a blacklist CSV file and generates a report from it

## Installation
This assumes you already have the following installed: Python2.7 and pip

This will install the dependencies for the application
```
> pip install -r requirements.txt
```

## Usage
```
> ./blacklist_parser.py --helpusage: blacklist_parser.py [-h] [--verbose] [--source SOURCE] [--dest DEST]
                           [--stdout]

optional arguments:
  -h, --help       show this help message and exit
  --verbose        output info and debug messages
  --source SOURCE  override default source for blacklist CSV file
  --dest DEST      override default filename for generated report. Ignored if
                   stdout option used
  --stdout         Write report to stdout rather than to a file

```
