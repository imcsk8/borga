# -*- coding: utf-8 -*-

import sys

from kobo.client import ClientCommand

from borga.lib.connectors import BZConnector


class Set_Modified(ClientCommand):
    """sets bugs to state MODIFIED"""
    enabled = True

    def options(self):
        self.parser.usage = ('%%prog %s [options] <product> <component>'
                             % self.normalized_name)
        self.parser.add_option('-b',  '--bugs',
                               action='store',
                               dest='bugs',
                               default=None,
                               help=('comma separated list of bugs '
                                     'to set to MODIFIED'))
        self.parser.add_option('-o', '--owner',
                               action='store',
                               dest='owner',
                               default=None,
                               help=('update only bugs assigned '
                                     'to given user'))
        self.parser.add_option('-f', '--fixed-in',
                               action='store',
                               dest='fixed_in',
                               default=None,
                               help='fill "Fixed in" with given value')
        self.parser.add_option('-c', '--comment',
                               action='store',
                               dest='comment',
                               default=None,
                               help='comment the change in Bugzilla')

    def run(self, *args, **kwargs):
        try:
            product, component = args
        except ValueError:
            self.parser.error('Please specify product and component.')
        owner = kwargs.get('owner')
        fixed_in = kwargs.get('fixed_in')
        comment = kwargs.get('comment')
        bugs = [i.strip()
                for i in kwargs.get('bugs', '').split(',')
                if i.strip()]

        url = self.conf.get('SERVICE')
        user = self.conf.get('USERNAME')
        password = self.conf.get('PASSWORD')
        bzconn = BZConnector(url, user=user, password=password)

        modified = []
        kwargs = {'product': product, 'component': component,
                  'assigned_to': owner, 'status': pre_status}
        for bug in bzconn.get_bugs(**kwargs):
            if bugs and str(bug.bug_id).strip() not in bugs:
                continue
            self.update_bug(bug, fixed_in=fixed_in, status=post_status,
                             comment=comment)
            modified.append(bug.bug_id)
        bug_out = ', '.join(['rhbz#%s' % i for i in modified])
        sys.stdout.write('Modified: %s\n' % bug_out)
