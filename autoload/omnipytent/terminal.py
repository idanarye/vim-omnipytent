import vim
import re

from .execution import FN, ShellCommandExecuter
from .util import other_windows, vim_repr
from .async_execution import AsyncCommand


class Terminal(ShellCommandExecuter):
    def __init__(self, job_id, buffer):
        self.job_id = job_id
        self.buffer = buffer

    if bool(int(vim.eval('exists("*term_start")'))):  # Vim 8
        @staticmethod
        def __start(command):
            job_id = FN.term_start(command, dict(
                curwin=1,
                out_cb=FN['omnipytent#_vimJobChannelCallbackStdout'],
                err_cb=FN['omnipytent#_vimJobChannelCallbackStderr'],
                exit_cb=FN['omnipytent#_vimJobExitCallback'],
            ))
            return job_id

        def write(self, text):
            # FN won't work - term_sendkeys's result is weird
            vim.command('call term_sendkeys(%s, %s)' % (self.job_id, vim_repr(text)))
            for window in vim.windows:
                if window.buffer != self.buffer:
                    continue
                if window.valid:
                    with other_windows(window):
                        # Unlike Neovim's, with Vim 8's terminal you need to enter
                        # insert mode inside the terminal after sending the keys.
                        vim.command(r'call feedkeys("a\<C-\>\<C-n>G", "n")')

        @property
        def alive(self):
            return FN.string(FN.term_getjob.raw_call(self.job_id)).endswith(' run')

    elif bool(int(vim.eval('exists("*termopen")'))):  # Neovim
        @staticmethod
        def __start(command):
            callback = FN['omnipytent#_nvimJobCallback']
            job_id = FN.termopen(command, dict(
                on_stdout=callback,
                on_stderr=callback,
                on_exit=callback,
            ))
            FN.feedkeys('a', 'n')
            try:
                vim.command('normal! G')
            except:
                pass
            return job_id

        def write(self, text):
            FN.jobsend(self.job_id, text)

        @property
        def alive(self):
            try:
                FN.jobsend(self.job_id, '')
            except Exception:
                return False
            else:
                return True

    def send_raw(self, text):
        self.write(text + '\n')

    try:
        __start
    except NameError:
        pass
    else:
        @classmethod
        def start(cls, command):
            return cls(cls.__start(command), vim.current.buffer)

    def wait_for_prompt(self, target):
        return TerminalWaitForOutputCommand(self, target, allow_partial=True)

    def wait_for_prompt_regex(self, target):
        return TerminalWaitForOutputCommand(self, re.compile(target), allow_partial=True)


class TerminalYieldedCommand(AsyncCommand):
    def __init__(self, terminal):
        self.terminal = terminal
        self.buffer = []

    def on_yield(self):
        FN['omnipytent#_registerYieldedCommandForJob'](self.terminal.job_id, self.vim_obj)

    def resume(self, returned_value=None):
        FN['omnipytent#_unregisterYieldedCommandForJob'](self.terminal.job_id)
        super(TerminalYieldedCommand, self).resume(returned_value=returned_value)

    def handle_text_output(self, channel, data):
        for chunk in data:
            self.buffer.append(chunk)
            self.on_line_parts_received(self.buffer)
            if chunk.endswith('\r') or chunk.endswith('\n'):
                line = ''.join(self.buffer).rstrip('\r\n')
                print('will clear buffer %s', self.buffer)
                del self.buffer[:]
                self.on_line_received(line)

    def handle_exit(self, returncode):
        pass

    def on_line_received(self, line):
        pass

    def on_line_parts_received(self, line_parts):
        pass


class TerminalWaitForOutputCommand(TerminalYieldedCommand):
    def __init__(self, terminal, target, allow_partial):
        super(TerminalWaitForOutputCommand, self).__init__(terminal)

        self.target = target
        self.allow_partial = allow_partial

        self._set_predicate()

    def _set_predicate(self):
        if isinstance(self.target, str):
            self.predicate = lambda txt: self.target in txt
        elif isinstance(self.target, re.Pattern):
            self.predicate = self.target.search
        elif callable(self.target):
            self.predicate = self.target

    def on_line_received(self, line):
        if self.allow_partial:
            return

    def on_line_parts_received(self, line_parts):
        if not self.allow_partial:
            return
        if self.predicate(''.join(line_parts)):
            self.run_next_frame('resume')
