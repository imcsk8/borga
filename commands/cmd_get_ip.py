# -*- coding: utf-8 -*-

import sys
from lxml.cssselect import CSSSelector
from lxml.etree import fromstring

from kobo.client import ClientCommand
from kobo.shortcuts import run

from borga.lib.connectors import BZConnector


def get_ip_from_leases(mac):
    cmd = ('cat /var/lib/libvirt/dnsmasq/default.leases |'
           'grep "%s"' % mac)
    rc, out = run(cmd, can_fail=True)
    if int(rc):
        return None
    return out.split(' ')[2]


def get_mac(name):
    cmd = ('sudo virsh dumpxml "%s"' % name)
    rc, out = run(cmd, can_fail=True)
    if int(rc):
        return None
    content = fromstring(out)

    output = []
    ifsel = CSSSelector('interface[type="network"]')
    macsel = CSSSelector('mac')
    for interface in ifsel(content):
        hwaddr = macsel(interface)[0]
        output.append(hwaddr.get('address'))
    return output


class Get_Ip(ClientCommand):
    """
    Returns IP address of local libvitr VM. Note that for this
    command passwordless sudo is required
    """
    enabled = True

    def options(self):
        self.parser.usage = '%%prog %s <name>' % self.normalized_name

    def run(self, *args, **kwargs):
        try:
           name = args[0]
        except ValueError:
            self.parser.error('Please specify pname of VM.')

        macs = get_mac(name)
        if not macs:
            self.parser.error('Unable to find out MAC address of VM')
        ips = [get_ip_from_leases(i) for i in macs
                                     if get_ip_from_leases(i)]
        if not ips:
            self.parser.error('Unable to find out IP address from '
                              '/var/lib/libvirt/dnsmasq/default.leases')
        for i in ips:
            sys.stdout.write('%s\n' % i)
        sys.stdout.flush()
