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
            job_id = FN.term_start(command, dict(curwin=1))
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
                        vim.command(r'call feedkeys("a\<C-\>\<C-n>", "n")')
    elif bool(int(vim.eval('exists("*termopen")'))):  # Neovim
        @staticmethod
        def __start(command):
            callback = FN['omnipytent#_nvimTerminalCallback']
            job_id = FN.termopen(command, dict(
                on_stdout=callback,
                on_stderr=callback,
                on_exit=callback,
            ))
            FN.feedkeys('a', 'n')
            vim.command('normal! G')
            return job_id

        def write(self, text):
            FN.jobsend(self.job_id, text)

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

    def wait_for_prompt(self, target, channels={'stdout', 'stderr'}):
        return TerminalWaitForOutputCommand(self, target, allow_partial=True, channels=channels)

    def wait_for_prompt_regex(self, target, channels={'stdout', 'stderr'}):
        return TerminalWaitForOutputCommand(self, re.compile(target), allow_partial=True, channels=channels)


class TerminalYieldedCommand(AsyncCommand):
    def __init__(self, terminal):
        self.terminal = terminal
        self.buffers = dict(stderr=[], stdout=[])

    def on_yield(self):
        FN['omnipytent#_registerYieldedCommandForJob'](self.terminal.job_id, self.vim_obj)

    def resume(self, returned_value=None):
        FN['omnipytent#_unregisterYieldedCommandForJob'](self.terminal.job_id)
        super().resume(returned_value=returned_value)

    def handle_text_output(self, channel, data):
        buf = self.buffers[channel]
        for chunk in data:
            buf.append(chunk)
            self.on_line_parts_received(channel, buf)
            if chunk.endswith('\r') or chunk.endswith('\n'):
                line = ''.join(buf).rstrip('\r\n')
                buf.clear()
                self.on_line_received(channel, line)

    def handle_exit(self):
        pass

    def on_line_received(self, channel, line):
        pass

    def on_line_parts_received(self, channel, line_parts):
        pass


class TerminalWaitForOutputCommand(TerminalYieldedCommand):
    def __init__(self, terminal, target, allow_partial, channels):
        super().__init__(terminal)

        self.target = target
        self.allow_partial = allow_partial
        if isinstance(self.channels, str):
            channels = {self.channels}
        else:
            channels = set(self.channels)
        self.channels = channels

        self._set_predicate()

    def _set_predicate(self):
        if isinstance(self.target, str):
            self.predicate = lambda txt: self.target in txt
        elif isinstance(self.target, re.Pattern):
            self.predicate = self.target.search
        elif callable(self.target):
            self.predicate = self.target

    def on_line_received(self, channel, line):
        if self.allow_partial:
            return
        if channel not in self.channels:
            return

    def on_line_parts_received(self, channel, line_parts):
        if not self.allow_partial:
            return
        if channel not in self.channels:
            return
        if self.predicate(''.join(line_parts)):
            self.run_next_frame('resume')
