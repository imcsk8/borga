# -*- coding: utf-8 -*-

import fcntl
import os
import pexpect
import signal
import struct
import sys
import termios

from lxml.cssselect import CSSSelector
from lxml.etree import fromstring

from kobo.client import ClientCommand
from kobo.shortcuts import run


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


def sigwinch_passthrough(sig, data):
    # Check for buggy platforms (see pexpect.setwinsize()).
    if 'TIOCGWINSZ' in dir(termios):
        TIOCGWINSZ = termios.TIOCGWINSZ
    else:
        TIOCGWINSZ = 1074295912 # assume
    s = struct.pack ("HHHH", 0, 0, 0, 0)
    a = struct.unpack ('HHHH', fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ , s))
    global global_pexpect_instance
    global_pexpect_instance.setwinsize(a[0],a[1])


class Ssh(ClientCommand):
    """
    Returns IP address of local libvitr VM. Note that for this
    command passwordless sudo is required
    """
    enabled = True

    def options(self):
        self.parser.usage = '%%prog %s <name>' % self.normalized_name

    def run(self, *args, **kwargs):
        mac = get_mac(args[0])
        if not mac:
            print 'Unable to find out MAC address of %s' % name
            sys.exit(1)
        ip = get_ip_from_leases(mac)
        if not ip:
            print ('Unable to find out IP address of %s from '
                   '/var/lib/libvirt/dnsmasq/default.leases'
                   % name)
            sys.exit(1)

        ssh_newkey = 'Are you sure you want to continue connecting'
        p = pexpect.spawn('ssh -o StrictHostKeyChecking=no '
                              '-o UserKnownHostsFile=/dev/null %s' % ip)
        i = p.expect([ssh_newkey, 'password:',
                      pexpect.EOF, pexpect.TIMEOUT],1)
        if i == 0:
            p.sendline('yes')
            i = p.expect([ssh_newkey, 'password:', pexpect.EOF])
        if i == 1:
            passwd = self.conf.get('VM_PASSWORD')
            if passwd:
                p.sendline(passwd)
        p.sendline("\r")
        global global_pexpect_instance
        global_pexpect_instance = p
        signal.signal(signal.SIGWINCH, sigwinch_passthrough)

        try:
            p.interact()
            sys.exit(0)
        except:
            sys.exit(1)
