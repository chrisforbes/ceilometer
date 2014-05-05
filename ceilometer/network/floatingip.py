# -*- encoding: utf-8 -*-
#
# Copyright © 2012 eNovance <licensing@enovance.com>
#
# Copyright 2013 IBM Corp
# All Rights Reserved.
#
# Author: Julien Danjou <julien@danjou.info>
# Author: Chris Forbes <chrisf@ijw.co.nz>
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

from oslo.config import cfg
from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils

from ceilometer.central import plugin
from ceilometer import sample
from neutronclient.v2_0.client import Client as NeutronClient


class FloatingIPPollster(plugin.CentralPollster):

    LOG = log.getLogger(__name__ + '.floatingip')

    def _get_floating_ips(self, manager):
        ksclient = manager.keystone
        endpoint = ksclient.service_catalog.url_for(
            service_type='network',
            endpoint_type=cfg.CONF.service_credentials.os_endpoint_type)
        neutron = NeutronClient(
            endpoint_url=endpoint,
            token=ksclient.auth_token)

        return neutron.list_floatingips()['floatingips']

    def _iter_floating_ips(self, manager, cache):
        if 'floating_ips' not in cache:
            cache['floating_ips'] = list(self._get_floating_ips(manager))
        return iter(cache['floating_ips'])

    def get_samples(self, manager, cache):
        for ip in self._iter_floating_ips(manager, cache):
            self.LOG.info("FLOATING IP USAGE: %s" % ip)
            # HACK (chrisf) Since nova has some issues providing all the things
            # we want here, use the neutron API instead, which has no problem
            # providing all the allocated floating IPs along with their tenant
            # info.
            yield sample.Sample(
                name='ip.floating',
                type=sample.TYPE_GAUGE,
                unit='ip',
                volume=1,
                user_id=None,
                project_id=ip['tenant_id'],
                resource_id=ip['id'],
                timestamp=timeutils.utcnow().isoformat(),
                resource_metadata={
                    'address': ip['floating_ip_address'],
                })
