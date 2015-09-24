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


def parse_header(header):
    '''get the report name and time from the header'''
    if len(header) < 3:
        logger.error("Blacklist header too short")
        return None, None

    report_name = header[1].strip('#').strip(' ')
    report_timestamp = header[2].strip('#').strip(' ')
    report_datetime = None
    try:
        report_datetime = datetime.datetime.strptime(report_timestamp,
                                                     "Last updated: %Y-%m-%d %H:%M:%S (%Z)")
    except ValueError:
        logger.error("Timestamp in blacklist not formatted as expected: %s", report_timestamp)
        logger.debug(traceback.format_exc())

    return report_name, report_datetime
#end parse_header


def parse_trailer(trailer):
    '''get the data count from the trailer'''
    parsed_trailer = re.match(r"# Number of entries: ([0-9]+)", trailer)
    if parsed_trailer:
        num_entries = int(parsed_trailer.group(1))
    else:
        logger.error("Trailer in blacklist not formatted as expected")
        num_entries = -1

    return num_entries
#end parse_trailer


def generate_report(report, report_name, num_entries, report_datetime, blacklist_dict):
    """Write the data to the report

    Args:
        report: Stream to write the report to. Usually an open file.
        report_name: Name of the blacklist report
        num_entires: Integer representing number of entries in the blacklist
        report_datetime: datetime object from timestamp in the blacklist
        blacklist_dict: dict with the blacklist data.
           example: {"KINS C&C": [(89.65.63.95,443),
                                  (91.214.209.193,443)],
                     "Dridex C&C": [(91.201.155.96,443)]}
        """

    report.write("%s Blacklist Report\n" % report_name)
    report.write("(%d IP's found at %s):\n" % (num_entries,
                                             report_datetime.strftime("%b %d %H:%M:%S %Y")))

    # Write out each section in alphabetical order
    for description in sorted(blacklist_dict.keys()):
        entries = blacklist_dict[description]
        report.write("\n=== %s ===\n" % description)
        for entry in entries:
            report.write(':'.join(entry) + "\n")

#end generate_report



def parse_blacklist(data, report):
    """Extract data from blacklist and create a report

    Parses the necessary data from the input and writes out a report

    Args:
        data: String containing the retrieved blacklist report
        report: Stream to write the report to. Usually an open file.
        """

    logger.info("parse_blacklist")

    field_list = "# DstIP,DstPort\n"
    header_end = data.find(field_list)
    if not header_end:
        logger.error("CSV File Header does not conform to expected formatting")
        return

    # Parse the file header
    report_name, report_datetime = parse_header(data[:header_end].splitlines())

    blacklist_dict = defaultdict(list)
    # get all the rows of data that appear after the header block
    rows = data[header_end+len(field_list):].splitlines()

    # Remove trailer from data list and parse it
    num_entries = parse_trailer(rows.pop())

    # Walk the list of rows
    try:
        reader = csv.reader(rows)
        for row in reader:
            if len(row) != 3:
                logger.error("Skipping invalid data row: %s", str(row))
                continue

            dest_IP, dest_port, description = row
            blacklist_dict[description].append((dest_IP, dest_port))
    except csv.Error:
        logger.error("CSV parsing failed for blacklist")
        logger.debug(traceback.format_exc())

    generate_report(report, report_name, num_entries, report_datetime, blacklist_dict)
#end parse_blacklist



def main():
    """Retrieve CSV blacklist and generates report"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="output info and debug messages",
                        action="store_true")
    parser.add_argument("--source", help="override default source for blacklist CSV file",
                        default="https://sslbl.abuse.ch/blacklist/sslipblacklist.csv")
    parser.add_argument("--dest", help="override default filename for generated report. Ignored if stdout option used",
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
        try:
            report = open(args.dest, 'w')
        except IOError:
            logger.error("Failed to open report output file")
            logger.debug(traceback.format_exc())

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging_level)
    logger.info('Starting blacklist parser')
    try:
        data = get_blacklist(args.source)
        parse_blacklist(data, report)
    except Exception: #catch-all in case something falls through
        logger.error(traceback.format_exc())
    finally:
        report.close()

    logger.info('Finished blacklist parser')
#end main

if __name__ == '__main__':
    main()
