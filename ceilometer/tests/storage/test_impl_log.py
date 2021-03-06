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
"""Tests for ceilometer/storage/impl_log.py
"""

import mock

from ceilometer.openstack.common import test
from ceilometer.storage import impl_log


class ConnectionTest(test.BaseTestCase):
    def test_get_connection(self):
        conf = mock.Mock()
        log_stg = impl_log.LogStorage()
        conn = log_stg.get_connection(conf)
        conn.record_metering_data({'counter_name': 'test',
                                   'resource_id': __name__,
                                   'counter_volume': 1,
                                   })
