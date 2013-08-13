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
        for name in args:
            macs = get_mac(name)
            if not macs:
               print 'Unable to find out MAC address of %s' % name
               continue
            ips = [get_ip_from_leases(i) for i in macs
                                         if get_ip_from_leases(i)]
            if not ips:
                print ('Unable to find out IP address of %s from '
                       '/var/lib/libvirt/dnsmasq/default.leases'
                       % name)
                continue
            for i in ips:
                sys.stdout.write('%s: %s\n' % (name,i))
            sys.stdout.flush()
