import vim

from itertools import chain

try:
    from shlex import quote
except ImportError:
    from pipes import quote

from .util import vim_repr


class VimCommand:
    _quoter = str

    def __init__(self, command):
        self._command = command

    def __call__(self, *args):
        vim.command(' '.join(chain([self._command], map(self._quoter, args))))

    @property
    def bang(self):
        return self.__class__('%s!' % self._command)


class CMD:
    def __getattr__(self, command):
        return VimCommand(command)

    def __getitem__(self, command):
        return VimCommand(command)

CMD = CMD()


class VimFunction:
    def __init__(self, function):
        self._function = function

    __number_type = vim.eval('type(0)')
    __float_type = vim.eval('type(0.0)')

    def __call__(self, *args):
        func_expr = '%s(%s)' % (self._function, ', '.join(map(vim_repr, args)))
        # print(func_expr)
        # print('map(%s, "v:val, v:val"' % func_expr)
        result_type, result_value = vim.eval('map([%s], "[type(v:val), v:val]")[0]' % func_expr)
        if result_type == self.__number_type:
            result_value = int(result_value)
        elif result_type == self.__float_type:
            result_value = float(result_value)
        return result_value


class FN:
    def __getattr__(self, function):
        return VimFunction(function)

    def __getitem__(self, function):
        return VimFunction(function)

FN = FN()


class ShellCommandExecuter:
    def __init__(self, func):
        self._func = func

    def __call__(self, *args):
        return self._func(' '.join(quote(str(arg)) for arg in args))


@ShellCommandExecuter
def BANG(command):
    vim.command('!%s' % command)
    return int(vim.eval('v:shell_error'))


@ShellCommandExecuter
def SH(command):
    vim.command('!%s' % command)
    shell_error = int(vim.eval('v:shell_error'))
    if shell_error:
        raise Exception('Shell error %s while executing `%s`' % (shell_error, command))


if bool(int(vim.eval('exists(":terminal")'))):
    @ShellCommandExecuter
    def TERMINAL_TAB(command):
        vim.command('tabnew')
        vim.command('terminal %s' % command)

    def TERMINAL_PANEL(command):
        vim.command('redraw')  # Release 'Press ENTER or type command to continue'
        old_win_view = vim.eval('winsaveview()')
        vim.command('botright new')
        vim.command('call winrestview(%s)' % old_win_view)
        vim.command('resize 5')
        vim.command('terminal %s' % command)
        vim.command('autocmd BufWinLeave <buffer> execute winnr("#")."wincmd w"')

