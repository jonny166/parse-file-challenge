#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Parser for https://sslbl.abuse.ch/blacklist/sslipblacklist.csv
Command-line application that retrieves parses the CSV blacklist and generates a report
Usage:
  $ python blacklist_parser.py
You can also get help on all the command-line flags the program understands
by running:
  $ python blacklist_parser.py --help
To get detailed log output run:
  $ python blacklist_parser.py --logging_level=DEBUG
"""
from __future__ import print_function

__author__ = 'kathy.church@gmail.com (Kathy Church)'
__version__ = "1.0"

import argparse
from collections import defaultdict
import csv
import datetime
import logging
import re
import requests
import sys
import traceback

logger = logging.getLogger(__name__)

def get_blacklist(source):
    '''Retrieve blacklist data'''
    logger.info("get_blacklist: %s", source)

    try:
        response = requests.get(source)
        if len(response.text) > 0:
            return response.text
        else:
            logger.error("Retrieved empty blacklist file")
            return None

    except requests.exceptions.RequestException as e:
        logger.error("Blacklist retrieval failed. %s", str(e))
        logger.debug(traceback.format_exc())
        return None

#end get_blacklist


def generate_report(csv_data, report):
    '''Convert CSV data to report'''
    logger.info("generate_report")
    
    field_list = "# DstIP,DstPort"
    header_end = csv_data.find(field_list)
    if not header_end:
        logger.error("CSV File Header does not conform to expected formatting")
        return

    # Parse the file header
    header = csv_data[:header_end].splitlines()
    report_name = header[1].strip('#').strip(' ')
    report_timestamp = header[2].strip('#').strip(' ')
    report_datetime = datetime.datetime.strptime(report_timestamp, 
                                                 "Last updated: %Y-%m-%d %H:%M:%S (%Z)")

    blacklist_dict = defaultdict(list)
    # get all the rows of data that appear after the header block
    rows = csv_data[header_end+len(field_list):].splitlines()

    # Remove trailer from data list and parse it
    trailer = rows.pop()
    parsed_trailer = re.match(r"# Number of entries: ([0-9]+)", trailer)
    num_entries = int(parsed_trailer.group(1))

    report.write("%s Blacklist Report\n" % report_name)
    report.write("(%d IP's found at %s):\n" % (num_entries, 
                                             report_datetime.strftime("%b %d %H:%M:%S %Y")))

    # Walk the list of rows
    reader = csv.reader(rows)
    for row in reader:
        if len(row) != 3:
            logger.error("Skipping invalid data row: %s", str(row))
            continue

        destIP, destPort, description = row
        blacklist_dict[description].append((destIP, destPort))

    # Write out each section in alphabetical order
    for description in sorted(blacklist_dict.keys()):
        entries = blacklist_dict[description]
        report.write("\n=== %s ===\n" % description)
        for entry in entries:
            report.write(':'.join(entry) + "\n")

#end generate_report



def main():
    '''Retrieve CSV blacklist and generate report'''

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="output info and debug messages",
                        action="store_true")
    parser.add_argument("--source", help="source for blacklist CSV file",
                        default="https://sslbl.abuse.ch/blacklist/sslipblacklist.csv")
    parser.add_argument("--dest", help="filename for generated report. Ignored if stdout option used",
                        default="sslbl_abuse_blacklist_%s.report" % datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    parser.add_argument("--stdout", help="Write report to stdout rather than to a file",
                        action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.ERROR
        
    if args.stdout:
        report = sys.stdout
    else:
        report = open(args.dest, 'w')

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging_level)
    logger.info('Starting blacklist parser')
    try:
        data = get_blacklist(args.source)
        generate_report(data, report)
    except Exception, e:
        logger.error(traceback.format_exc())
        
    report.close()
    logger.info('Finished blacklist parser')
#end main

if __name__ == '__main__':
    main()
