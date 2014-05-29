# -*- encoding: utf-8 -*-
#
# Copyright © 2014 Catalyst IT
#
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
from cinderclient.client import Client as CinderClient


class VolumeSizePollster(plugin.CentralPollster):

    LOG = log.getLogger(__name__ + '.volumesize')

    def _get_volumes(self, manager):
        ksclient = manager.keystone
        endpoint = ksclient.service_catalog.url_for(
            service_type='volume',
            endpoint_type=cfg.CONF.service_credentials.os_endpoint_type)

        # Cinder client is a bit bogus wrt use of an existing token.
        cinder = CinderClient('1', None, None, ksclient.tenant_name)
        cinder.client.management_url = endpoint
        cinder.client.auth_token = ksclient.auth_token

        return cinder.volumes.list(search_opts={'all_tenants': True})

    def _iter_volumes(self, manager, cache):
        if 'volumes' not in cache:
            cache['volumes'] = list(self._get_volumes(manager))
        return iter(cache['volumes'])

    def get_samples(self, manager, cache):
        for volume in self._iter_volumes(manager, cache):
            self.LOG.info("VOLUME USAGE %s" % volume)
            yield sample.Sample(
                name='volume.size',
                type=sample.TYPE_GAUGE,
                unit='GB',
                volume=volume.size,
                user_id=None,
                project_id=getattr(volume, 'os-vol-tenant-attr:tenant_id'),
                resource_id=volume.id,
                timestamp=timeutils.utcnow().isoformat(),
                resource_metadata={
                    'display_name': volume.display_name,
                    'volume_type': volume.volume_type
                })

