import vim

from .execution import FN, ShellCommandExecuter
from .util import other_windows, vim_repr


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
            job_id = FN.termopen(command)
            FN.feedkeys('a', 'n')
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
