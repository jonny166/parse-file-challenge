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
import csv
import datetime
import logging
import requests
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


def generate_report(csv_data, report_filename):
    '''Convert CSV data to report'''
    logger.info("generate_report: %s", report_filename)
    # TODO: Generate report file
#end generate_report

def main():
    '''Retrieve CSV blacklist and generate report'''

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="output info and debug messages",
                        action="store_true")
    parser.add_argument("--source", help="source for blacklist CSV file",
                        default="https://sslbl.abuse.ch/blacklist/sslipblacklist.csv")
    parser.add_argument("--dest", help="filename for generated report",
                        default="sslbl_abuse_blacklist_%s.report" % datetime.datetime.now().strftime("%Y%M%d%H%m%S"))

    args = parser.parse_args()

    if args.verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.ERROR

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging_level)
    logger.info('Starting blacklist parser')
    try:
        data = get_blacklist(args.source)
        generate_report(data, args.dest)
    except Exception, e:
        logger.error(traceback.format_exc())
        
    logger.info('Finished blacklist parser')
#end main

if __name__ == '__main__':
    main()
