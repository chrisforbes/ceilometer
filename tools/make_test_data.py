#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Command line tool for creating test data for ceilometer.
"""
from __future__ import print_function

import argparse
import datetime
import logging
import sys

from oslo.config import cfg

from ceilometer.publisher import utils
from ceilometer import sample
from ceilometer import storage
from ceilometer.openstack.common import timeutils


def main():
    cfg.CONF([], project='ceilometer')

    parser = argparse.ArgumentParser(
        description='generate metering data',
    )
    parser.add_argument(
        '--interval',
        default=10,
        type=int,
        help='The period between events, in minutes.',
    )
    parser.add_argument(
        '--start',
        default=31,
        help='The number of days in the past to start timestamps.',
    )
    parser.add_argument(
        '--end',
        default=2,
        help='The number of days into the future to continue timestamps.',
    )
    parser.add_argument(
        '--type',
        choices=('gauge', 'cumulative'),
        default='gauge',
        help='Counter type.',
    )
    parser.add_argument(
        '--unit',
        default=None,
        help='Counter unit.',
    )
    parser.add_argument(
        '--project',
        help='Project id of owner.',
    )
    parser.add_argument(
        '--user',
        help='User id of owner.',
    )
    parser.add_argument(
        'resource',
        help='The resource id for the meter data.',
    )
    parser.add_argument(
        'counter',
        help='The counter name for the meter data.',
    )
    parser.add_argument(
        'volume',
        help='The amount to attach to the meter.',
        type=int,
        default=1,
    )
    args = parser.parse_args()

    # Set up logging to use the console
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    root_logger = logging.getLogger('')
    root_logger.addHandler(console)
    root_logger.setLevel(logging.DEBUG)

    # Connect to the metering database
    conn = storage.get_connection(cfg.CONF)

    # Find the user and/or project for a real resource
    if not (args.user or args.project):
        for r in conn.get_resources():
            if r['resource_id'] == args.resource:
                args.user = r['user_id']
                args.project = r['project_id']
                break

    # Compute start and end timestamps for the
    # new data.
    timestamp = timeutils.parse_isotime(args.start)
    end = timeutils.parse_isotime(args.end)
    increment = datetime.timedelta(minutes=args.interval)

    # Generate events
    n = 0
    while timestamp <= end:
        c = sample.Sample(name=args.counter,
                            type=args.type,
                            unit=args.unit,
                            volume=args.volume,
                            user_id=args.user,
                            project_id=args.project,
                            resource_id=args.resource,
                            timestamp=timestamp,
                            resource_metadata={},
                            source='artificial',
                            )
        data = utils.meter_message_from_counter(
            c,
            cfg.CONF.publisher.metering_secret)
        conn.record_metering_data(data)
        n += 1
        timestamp = timestamp + increment

    print('Added %d new events' % n)

    return 0

if __name__ == '__main__':
    main()
