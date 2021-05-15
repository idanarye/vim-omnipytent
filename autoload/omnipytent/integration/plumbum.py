from __future__ import absolute_import

from itertools import chain

import vim

from plumbum import local  # not used here, but users are expected to import it

from omnipytent.execution import ShellCommandExecuter, quote

__ENV_VARS_POSSIBLE_ATTR_NAMES = ('env', 'envvars')

def __get_env_vars(cmd):
    result = {}
    for attr_name in __ENV_VARS_POSSIBLE_ATTR_NAMES:
        env_vars = getattr(cmd, attr_name, None)
        if env_vars:
            result.update(env_vars)
    return result

if int(vim.eval('has("win32")')):
    def __format_env_vars(cmd):
        env_vars = __get_env_vars(cmd)
        if not env_vars:
            return

        yield 'cmd'
        yield '/c'
        yield quote(''.join('set %s=%s&&' % pair for pair in env_vars.items()))
else:
    def __format_env_vars(cmd):
        env_vars = __get_env_vars(cmd)
        if not env_vars:
            return

        for k, v in env_vars.items():
            yield '%s=%s' % (k, quote(v))


def __rand__(self, cmd):
    return self(*map(ShellCommandExecuter.Raw, chain(__format_env_vars(cmd),
                                                     cmd.formulate(1))))


ShellCommandExecuter.__rand__ = __rand__
