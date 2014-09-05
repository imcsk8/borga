# -*- coding: utf-8 -*-

import sys

from kobo.client import ClientCommand
from kobo.shortcuts import run

from borga.lib.connectors import BZConnector


def format_submodules(installdir, print_output=True):
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
            if line:
                sys.stdout.write('Invalid line: %s\n' % line)
            continue
        mod = {}
        mod['raw_url'] = cont[1].strip()
        mod['base_url'] = (mod['raw_url'].endswith('.git')
                                and mod['raw_url'][:-4]
                                or mod['raw_url'])
        mod['fullname'] = mod['base_url'].split('/')[-1]
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
            if line:
                sys.stdout.write('Invalid line: %s\n' % line)
            continue
        mod = modules[index]
        mod['path'] = cont[1].strip()
        mod['name'] = mod['path'].split('/')[-1]
        mod['github_url'] = fmt % mod
        mod['destination'] = '%s/%s' % (installdir, mod['name'])
        index += 1

    # sort according to name
    modules.sort(key=lambda x: x['name'])

    # get commit hashes
    cmd = ('git submodule status')
    rc, out = run(cmd, can_fail=True)

    index = 0
    for line in out.split('\n'):
        cont = line.strip().split(' ')
        # some modules just have one field
        if len(cont) < 2:
            if line:
                sys.stdout.write('Invalid line: %s\n' % line)
            continue
        for mod in modules:
            if mod['path'] == cont[1].strip():
                mod['index'] = index
                mod['commit'] = cont[0].strip()
                import re
                if re.search("^\-|^\+", mod['commit']):
                    mod['commit'] = mod['commit'][1:]
                url = mod['github_url'].replace('%%{%(name)s_commit}' % mod,
                                                mod['commit'])
                mod['download_url'] = url.replace('git://', 'https://')

        index += 1

    # print output
    if print_output:
        for head, fmt in [
                ('Globals:\n',
                 '%%global %(name)s_commit\t%(commit)s\n'),
                ('Source list:\n',
                 'Source%(index)s:\t%(github_url)s\n'),
                ('Installation script:\n',
                 'cp -r %(fullname)s-%%{%(name)s_commit} %(destination)s\n')]:
            sys.stdout.write(head)
            for mod in modules:
                try:
                    prefix, suffix = fmt.split('\t')
                except Exception:
                    sys.stdout.write(fmt % mod)
                else:
                    prefix = prefix % mod
                    suffix = suffix % mod
                    space = 30 - len(prefix) + len(suffix)
                    sys.stdout.write(
                        '%s %s' % (
                            prefix, suffix.rjust(space)
                        )
                    )
            sys.stdout.write('\n')
        sys.stdout.flush()
    return modules


def download_submodules(modules, destination):
    for mod in modules:
        rc, out = run('wget %(download_url)s' % mod,
                      can_fail=True, workdir=destination)
        if rc:
            sys.stdout.write('Failed to download %(fullname)s (%(commit)s)\n' % mod)
        else:
            sys.stdout.write('Downloaded %(fullname)s (%(commit)s)\n' % mod)
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
        self.parser.add_option('-i',  '--installdir',
                               action='store',
                               dest='installdir',
                               default=None,
                               help='path where modules will be installed')

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

        installdir = kwargs.get('installdir')
        destination = kwargs.get('destination')

        # run subcommand
        if command == 'submodules-format':
            return format_submodules(installdir)
            #return format_submodules(installdir, True)

        if command == 'submodules-download':
            modules = format_submodules(installdir, print_output=False)
            return download_submodules(modules, destination)

        #Fail if we issue an invalid command
        sys.stdout.write("Invalid command: %s" % command)
