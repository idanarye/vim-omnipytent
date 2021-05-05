from __future__ import absolute_import

from itertools import chain

import vim

from plumbum import local  # not used here, but users are expected to import it

from omnipytent.execution import ShellCommandExecuter, quote


if int(vim.eval('has("win32")')):
    def __format_env_vars(cmd):
        try:
            env_vars = cmd.env
        except AttributeError:
            return
        if not env_vars:
            return

        yield 'cmd'
        yield '/c'
        yield quote(''.join('set %s=%s&&' % pair for pair in env_vars.items()))
else:
    def __format_env_vars(cmd):
        try:
            env_vars = cmd.env
        except AttributeError:
            return
        if not env_vars:
            return

        for k, v in env_vars.items():
            yield '%s=%s' % (k, quote(v))


def __rand__(self, cmd):
    return self(*map(ShellCommandExecuter.Raw, chain(__format_env_vars(cmd),
                                                     cmd.formulate(1))))


ShellCommandExecuter.__rand__ = __rand__
