#  Copyright (c) 2015-2016 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import collections
import io
import json

from pylxd import Client, exceptions

from molecule import util
from molecule.driver import basedriver

LOG = util.get_logger(__name__)


class LxdDriver(basedriver.BaseDriver):
    def __init__(self, molecule):
        super(LxdDriver, self).__init__(molecule)
        self._lxd = Client()
        self._containers = self.molecule.config.config['lxd']['containers']
        self._provider = self._get_provider()
        self._platform = self._get_platform()

    @property
    def name(self):
        return 'lxd'

    @property
    def instances(self):
        created_containers = self._lxd.containers.all()
        created_container_names = [
            container.name
            for container in created_containers
        ]
        for container in self._containers:
            if container.get('name') in created_container_names:
                container['created'] = True
            else:
                container['created'] = False

        return self._containers

    @property
    def default_provider(self):
        return self._provider

    @property
    def default_platform(self):
        return self._platform

    @property
    def provider(self):
        return self._provider

    @property
    def platform(self):
        return self._platform

    @platform.setter
    def platform(self, val):
        self._platform = val

    @property
    def valid_providers(self):
        return [{'name': self.provider}]

    @property
    def valid_platforms(self):
        return [{'name': self.platform}]

    @property
    def ssh_config_file(self):
        return

    @property
    def ansible_connection_params(self):
        return {'user': 'root', 'connection': 'lxd'}

    @property
    def testinfra_args(self):
        return {
            'connection': 'lxd',
            'hosts': self.get_hosts(),
        }

    def get_hosts(self):
        container_names = []
        for container in self.instances:
            container_names.append(container['name'])
        return ",".join(container_names)

    @property
    def serverspec_args(self):
        return dict()

    def up(self, no_provision=True):
        self.molecule.state.change_state('driver', self.name)

        for container in self.instances:

            if (container['created'] is not True):
                LOG.warning('Creating container {}'.format(container['name']))
                lxd_container = self._lxd.containers.create(container, wait=True)
                lxd_container.ephemeral = True
                lxd_container.save()
                lxd_container.start()
                container['created'] = True
                util.print_success('Container created.')
            else:
                lxd_container = self._lxd.containers.get(container['name'])
                lxd_container.start()
                util.print_success('Container {} already running.'.format(container[
                    'name']))

    def destroy(self):
        for container in self.instances:
            if (container['created']):
                LOG.warning('Stopping container {} ...'.format(container[
                    'name']))
                # lxd containers have a bad habit of lingering. Make sure
                # they're gone before continuing.
                lxd_container = self._lxd.containers.get(container['name'])
                lxd_container.ephemeral = True
                lxd_container.save()
                lxd_container.stop()
                try:
                    while True:
                        self._lxd.containers.get(container['name'])
                except exceptions.LXDAPIException:
                    util.print_success('Removed container {}.'.format(container[
                        'name']))
                    container['created'] = False

    def status(self):
        Status = collections.namedtuple('Status', ['name', 'state', 'provider'])
        status_list = []
        for container in self.instances:
            name = container.get('name')
            if container.get('created'):
                lxd_container = self._lxd.containers.get(container['name'])
                status_list.append(
                    Status(
                        name=name,
                        state=lxd_container.status,
                        provider=self.provider))
            else:
                status_list.append(
                    Status(
                        name=name,
                        state="not_created",
                        provider=self.provider))

        return status_list

    def conf(self, vm_name=None, ssh_config=False):
        pass

    def inventory_entry(self, instance):
        template = '{} connection=lxd\n'
        return template.format(instance['name'])

    def login_cmd(self, instance):
        return 'lxd exec {} bash'

    def login_args(self, instance):
        return [instance]

    def _get_platform(self):
        return 'lxd'

    def _get_provider(self):
        return 'lxd'
