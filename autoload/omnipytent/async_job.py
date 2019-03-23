import vim

from .execution import FN, ShellCommandExecuter
from .async_execution import AsyncCommand


class AsyncJob(AsyncCommand):
    def __init__(self, command):
        self._register()
        self._job = self.__create_job_object(command)
        FN['omnipytent#_registerYieldedCommandForJob'](self._job, self.vim_obj)

    def on_yield(self):
        pass

    if bool(int(vim.eval('exists("*term_start")'))):  # Vim 8
        pass
    elif bool(int(vim.eval('exists("*termopen")'))):  # Neovim
        def __create_job_object(self, command):
            callback = FN['omnipytent#_nvimJobCallback']
            return FN.termopen(command, dict(
                on_stdout=callback,
                on_stderr=callback,
                on_exit=callback,
            ))

    def handle_text_output(self, data):
        print(data)
