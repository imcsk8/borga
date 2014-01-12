# -*- coding: utf-8 -*-

import sys

from kobo.client import ClientCommand
from kobo.shortcuts import run

from borga.lib.connectors import BZConnector


def format_submodules(print_output=True):
    """Returns formated git module urls in GitHub format and current commit
    hashes for SPEC file.
    """
    # get urls
    cmd = ('cat .gitmodules | grep "url"')
    rc, out = run(cmd, can_fail=True)

    modules = []
    for line in out.split('\n'):
        cont = line.strip().split('=')
        if len(cont) < 2:
            continue
        mod = {}
        mod['raw_url'] = cont[1].strip()
        mod['base_url'] = mod['raw_url'].rstrip('.git')
        modules.append(mod)

    # get path for modules and github url
    cmd = ('cat .gitmodules | grep "path"')
    rc, out = run(cmd, can_fail=True)

    index = 0
    fmt = ('%(base_url)s/archive/%%{%(name)s_commit}/'
           '%(name)s-%%{%(name)s_commit}.tar.gz')
    for line in out.split('\n'):
        cont = line.strip().split('=')
        if len(cont) < 2:
            continue
        mod = modules[index]
        mod['path'] = cont[1].strip()
        mod['name'] = mod['path'].split('/')[-1]
        mod['github_url'] = fmt % mod
        mod['index'] = index
        index += 1

    # get commit hashes
    cmd = ('git submodule status')
    rc, out = run(cmd, can_fail=True)

    for line in out.split('\n'):
        cont = line.strip().split(' ')
        if len(cont) < 3:
            continue
        for mod in modules:
            if mod['path'] == cont[1].strip():
                mod['commit'] = cont[0].strip()

    # print output
    if print_output:
        for fmt in ('%%global\t%(name)s_commit\t\t%(commit)s\n',
                    'Source%(index)s:\t%(github_url)s\n'):
            for mod in modules:
                sys.stdout.write(fmt % mod)
        sys.stdout.flush()
    return modules


def download_submodules(modules, destination):
    for mod in modules:
        url = mod['github_url'].replace('%%{%(name)s_commit}' % mod,
                                        mod['commit'])
        rc, out = run('wget %s' % url, can_fail=True, workdir=destination)
        sys.stdout.write('Downloaded %(name)s (%(commit)s)\n' % mod)
    sys.stdout.flush()


class Git(ClientCommand):
    """
    Git helpers
    """
    enabled = True

    def options(self):
        self.parser.usage = ('%%prog %s <command> <arg> [options]\n'
                             'Commands(arg): submodules-format, '
                                            'submodules-download'
                             % self.normalized_name)
        # filtering options
        self.parser.add_option('-d',  '--destination',
                               action='store',
                               dest='destination',
                               default=None,
                               help='path where modules should be downloaded')

    def run(self, *args, **kwargs):
        try:
            command = args[0]
        except ValueError:
            self.parser.error('Please specify command.')

        destination = kwargs.get('destination')

        # run subcommand
        if command == 'submodules-format':
            format_submodules()

        if command == 'submodules-download':
            download_submodules(format_submodules(print_output=False),
                                destination)
