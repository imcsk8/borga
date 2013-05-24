# -*- coding: utf-8 -*-

import sys

from kobo.client import ClientCommand

from borga.lib.connectors import BZConnector


class Format_Msg(ClientCommand):
    """format commit message for GIT"""
    enabled = True

    def options(self):
        self.parser.usage = ('%%prog %s [options] <product> <component>'
                             % self.normalized_name)
        self.parser.add_option('-f',  '--flags',
                               action='store',
                               dest='flags',
                               default=None,
                               help=('comma separated list of bug '
                                     'flags which diplayed bugs have to '
                                     'have in state +'))
        self.parser.add_option('-o', '--owner',
                               action='store',
                               dest='owner',
                               default=None,
                               help=('show only bugs assigned to given '
                                     'user'))
        self.parser.add_option('-s', '--state',
                               action='store',
                               dest='state',
                               default='POST',
                               help=('show only bugs in given state '
                                    '(by default POST)'))

    def run(self, *args, **kwargs):
        try:
            product, component = args
        except ValueError:
            self.parser.error('Please specify product and component.')
        owner = kwargs.get('owner')
        state = kwargs.get('state')
        flags = [i.strip()
                 for i in kwargs.get('flags', '').split(',')
                 if i.strip()]

        url = self.conf.get('SERVICE')
        user = self.conf.get('USERNAME')
        password = self.conf.get('PASSWORD')
        bzconn = BZConnector(url, user=user, password=password)

        kwargs = {'product': product, 'component': component,
                  'assigned_to': owner, 'status': state}
        bugs = bzconn.get_bugs(**kwargs)

        final = []
        if flags:
            flag_filter = bzconn.filter_by_flags(bugs, flags, '+')
            for bug in bugs:
                addit = True
                for flg, bzlist in flag_filter.iteritems():
                    if bug.bug_id not in bzlist:
                        addit = False
                        break
                if addit:
                    final.append(bug.bug_id)
        else:
            final = [bug.bug_id for bug in bugs]

        bug_out = ', '.join(['rhbz#%s' % i for i in final])
        sys.stdout.write('Resolves: %s\n' % bug_out)
