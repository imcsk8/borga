# -*- coding: utf-8 -*-

import os
import sys
from optparse import IndentedHelpFormatter

from kobo.cli import CommandOptionParser
from kobo.client import ClientCommandContainer
from kobo.client import commands
from kobo.conf import PyConfigParser

from borga import commands


__all__ = ('main',)


CONF_PATH = os.environ.get('BORGA_CONF', '~/.borga')


# register command plugins
class BorgaCommandContainer(ClientCommandContainer):
    pass
BorgaCommandContainer.register_module(commands, prefix='cmd_')


def main():
    conf = PyConfigParser()
    conf.load_from_file(os.path.expanduser(CONF_PATH))
    container = BorgaCommandContainer(conf=conf)
    formatter = IndentedHelpFormatter(max_help_position=60, width=120)
    parser = CommandOptionParser(command_container=container,
                                 formatter=formatter,
                                 default_command='help')
    parser.run()
    sys.exit(0)


if __name__ == '__main__':
    main()
