# -*- coding: utf-8 -*-

import sys

from kobo.client import ClientCommand

from borga.lib.connectors import BZConnector


class Check_Flags(ClientCommand):
    """checks if bug has all necessary flags in state +"""
    enabled = True

    def options(self):
        self.parser.usage = ('%%prog %s [options] <product> <component>'
                             % self.normalized_name)
        self.parser.add_option('-f',  '--flags',
                               action='store',
                               dest='flags',
                               default=None,
                               help=('comma separated list of bug '
                                     'flags to check'))
        self.parser.add_option('-o', '--owner',
                               action='store',
                               dest='owner',
                               default=None,
                               help=('show only bugs assigned to given '
                                     'user'))

    def run(self, *args, **kwargs):
        try:
            product, component = args
        except ValueError:
            self.parser.error('Please specify product and component.')
        owner = kwargs.get('owner')
        flags = [i.strip()
                 for i in kwargs.get('flags', '').split(',')
                 if i.strip()]

        url = self.conf.get('SERVICE')
        user = self.conf.get('USERNAME')
        password = self.conf.get('PASSWORD')
        bzconn = BZConnector(url, user=user, password=password)

        failed = bzconn.check_bugs(product, component, flags,
                                   owner=owner)
        for flag, bugs in failed.iteritems():
            bugs = ' '.join(['rhbz#%s' % i for i in bugs])
            sys.stdout.write('Flag %s failed: %s\n' % (flag, bugs))
        sys.stdout.flush()
