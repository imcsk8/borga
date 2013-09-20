# -*- coding: utf-8 -*-

import sys

from kobo.client import ClientCommand

from borga.lib.connectors import BZConnector


def status_set(connector, bugs, status, fixed_in=None, message=None):
    """Sets given bugs to given status"""
    for bug in bugs:
        connector.update_bug(bug, fixed_in=fixed_in, status=status,
                             comment=message)
        sys.stdout.write('Changed bug #%s (%s).\n' % (bug.bug_id,
                                                     bug.summary[:20]))
        sys.stdout.flush()


def flag_set(connector, bugs, flag):
    """Sets flag in given bugs"""
    for bug in bugs:
        connector.update_bug(bug, flags=[flag])
        sys.stdout.write('Changed bug #%s (%s).\n' % (bug.bug_id,
                                                   bug.summary[:20]))
        sys.stdout.flush()


def flag_check(connector, bugs, flags):
    """Prints which bugs does not have required flag"""
    for flag in flags:
        query = connector.filter_by_flags(bugs, [flag], negative=True)
        if query:
            sys.stdout.write('Bugs missing flag %s:\n' % flag)
            for bug in query:
                sys.stdout.write('#%s (%s)\n' % (bug.bug_id, bug.summary[:20]))
            sys.stdout.flush()


def format(connector, bugs, msg_type):
    """Prints bugs in format"""
    if msg_type == 'git':
        fmt = 'rhbz#%s'
        separator = ', '
        sys.stdout.write('Resolves: ')
    elif msg_type == 'spec':
        fmt = '- (#%s)'
        separator = '\n'
    sys.stdout.write(separator.join([fmt % i.bug_id for i in bugs]))
    sys.stdout.flush()


class Bug(ClientCommand):
    """manipulates bugs in Bugzilla"""
    enabled = True

    def options(self):
        self.parser.usage = ('%%prog %s <command> <arg> [options]'
                             % self.normalized_name)
        # filtering options
        self.parser.add_option('-p',  '--product',
                               action='store',
                               dest='product',
                               default=None,
                               help='name of product')
        self.parser.add_option('-c',  '--component',
                               action='store',
                               dest='component',
                               default=None,
                               help='name of component')
        self.parser.add_option('-b',  '--bugs',
                               action='store',
                               dest='bugs',
                               default=None,
                               help=('comma separated list of bugs to modify '
                                     'or check'))
        self.parser.add_option('-f',  '--flags',
                               action='store',
                               dest='flags',
                               default=None,
                               help='comma separated list of bug flags')
        self.parser.add_option('-o', '--owner',
                               action='store',
                               dest='owner',
                               default=None,
                               help='update only bugs assigned to given user')
        self.parser.add_option('-t', '--target',
                               action='store',
                               dest='target',
                               default=None,
                               help='target release')
        self.parser.add_option('-s', '--status',
                               action='store',
                               dest='status',
                               default=None,
                               help='current bug status')
        self.parser.add_option('-d', '--default',
                               action='store',
                               dest='default',
                               default=None,
                               help='use default values from config')
        # input options
        self.parser.add_option('-i', '--fixed-in',
                               action='store',
                               dest='fixed_in',
                               default=None,
                               help='fill "Fixed in" with given value')
        self.parser.add_option('-m', '--message',
                               action='store',
                               dest='message',
                               default=None,
                               help='comment the change in Bugzilla')

    def run(self, *args, **kwargs):
        try:
            command = args[0]
        except ValueError:
            self.parser.error('Please specify command.')
        cmd_arg = len(args) > 1 and args[1]
        # filtering options
        product = kwargs.get('product')
        component = kwargs.get('component')
        owner = kwargs.get('owner')
        target = kwargs.get('target')
        status = kwargs.get('status')
        default = kwargs.get('default')
        bugs = kwargs.get('bugs')
        bugs = bugs and [i.strip() for i in bugs.split(',') if i.strip()]
        flags =  kwargs.get('flags')
        flags = flags and [i.strip() for i in flags.split(',') if i.strip()]

        # input options
        fixed_in = kwargs.get('fixed_in')
        message = kwargs.get('message')

        # setup connector
        url = self.conf.get('SERVICE')
        user = self.conf.get('USERNAME')
        password = self.conf.get('PASSWORD')
        connector = BZConnector(url, user=user, password=password)

        # query bugs
        sys.stdout.write('Please wait, this might take time depending on '
                         'the query specification.\n')
        sys.stdout.flush()
        qargs = {'product': product, 'component': component, 'status': status,
                 'assigned_to': owner}
        if default:
            for opt, var, cnf in [('p', 'product', 'DEFAULT_PRODUCT'),
                                  ('c', 'component', 'DEFAULT_COMPONENT')]:
                if opt in default and qargs[var] is None:
                    qargs[var] = self.conf.get(cnf)
        query = connector.get_bugs(**qargs)
        if bugs:
            query = connector.filter_by_ids(query, bugs)
        if flags:
            query = connector.filter_by_flags(query, flags)
        if target:
            query = connector.filter_by_target(query, target)
        sys.stdout.write('Query finished.\n')
        sys.stdout.flush()

        # run subcommand
        if command == 'list':
            for bug in query:
                sys.stdout.write('%s\n' % bug)
            sys.exit(0)
        if command == 'status-set':
            if not cmd_arg:
                self.parser.error('Please specify new status in argument.')
            status_set(connector, query, cmd_arg,
                       fixed_in=fixed_in, message=message)
            sys.exit(0)
        if command == 'flag-set':
            if not cmd_arg:
                self.parser.error('Please specify flag in argument.')
            flag_set(connector, query, cmd_arg)
        if command == 'flag-check':
            if not cmd_arg:
                self.parser.error('Please specify flags in argument.')
            flg = set([i.strip() for i in cmd_arg.split(',') if i.strip()])
            flag_check(connector, query, flg)
