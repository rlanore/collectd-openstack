#!/usr/bin/env python
#
# vim: tabstop=4 shiftwidth=4

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Ricardo Rocha <ricardo@catalyst.net.nz>
#
# About this plugin:
#   Helper object for all plugins.
#
# collectd:
#   http://collectd.org
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml
#
from keystoneclient.v2_0 import Client as KeystoneClient

import collectd
import traceback

class Base(object):

    def __init__(self):
        self.username = 'admin'
        self.password = '123456'
        self.tenant = 'openstack'
        self.auth_url = 'http://api.example.com:5000/v2.0'
        self.verbose = False
        self.prefix = ''

    def get_keystone(self):
        """Returns a Keystone.Client instance."""
        return KeystoneClient(username=self.username, password=self.password, 
                tenant_name=self.tenant, auth_url=self.auth_url)

    def config_callback(self, conf):
        """Takes a collectd conf object and fills in the local config."""
        for node in conf.children:
            if node.key == "Username":
                self.username = node.values[0]
            elif node.key == "Password":
                self.password = node.values[0]
            elif node.key == "TenantName":
                self.tenant = node.values[0]
            elif node.key == "AuthURL":
                self.auth_url = node.values[0]
            elif node.key == "Verbose":
                if node.values[0] in ['True', 'true']:
                    self.verbose = True
            elif node.key == "Prefix":
                self.prefix = node.values[0]
            else:
                collectd.warning("%s: unknown config key: %s" % (self.prefix, node.key))

    def dispatch(self, stats):
        """
        Dispatches the given stats.
        
        stats should be something like:

        {'plugin': {'plugin_instance': {'type': {'type_instance': <value>, ...}}}}
        """
        if not stats:
            collectd.error("%s: failed to retrieve stats from glance" % self.prefix)
            return

        self.logverbose("dispatching %d new stats :: %s" % (len(stats), stats))
        try:
            for plugin in stats.keys():
                for plugin_instance in stats[plugin].keys():
                    for type in stats[plugin][plugin_instance].keys():
                        for type_instance in stats[plugin][plugin_instance][type].keys():
                            self.dispatch_value(plugin, plugin_instance, 
                                    type, type_instance,
                                    stats[plugin][plugin_instance][type][type_instance])
        except Exception as exc:
            collectd.error("%s: failed to dispatch values :: %s :: %s" 
                    % (self.prefix, exc, traceback.format_exc()))

    def dispatch_value(self, plugin, plugin_instance, type, type_instance, value):
        """Looks for the given stat in stats, and dispatches it"""
        self.logverbose("dispatching value %s.%s.%s.%s=%s" 
                % (plugin, plugin_instance, type, type_instance, value))
    
        val = collectd.Values(type='gauge')
        val.plugin=plugin
        val.plugin_instance=plugin_instance
        val.type_instance="%s-%s" % (type, type_instance)
        val.values=[value]
        val.dispatch()

    def read_callback(self):
        try:
            stats = self.get_stats()
        except Exception as exc:
            collectd.error("%s: failed to get stats :: %s :: %s" 
                    % (self.prefix, exc, traceback.format_exc()))
        self.dispatch(stats)

    def get_stats(self):
        collectd.error('Not implemented, should be subclassed')

    def logverbose(self, msg):
        if self.verbose:
            collectd.info("%s: %s" % (self.prefix, msg))

