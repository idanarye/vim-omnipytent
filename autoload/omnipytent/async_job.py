import vim

from .execution import FN, ShellCommandExecuter
from .async_execution import AsyncCommand


class AsyncJob(AsyncCommand):
    def __init__(self, command):
        self._buffers = {'stdout': [''], 'stderr': ['']}
        self._register()
        self._job = self.__create_job_object(command)
        FN['omnipytent#_registerYieldedCommandForJob'](self._job, self.vim_obj)

    def on_yield(self):
        pass

    if bool(int(vim.eval('exists("*job_start")'))):  # Vim 8
        def __create_job_object(self, command):
            return FN['omnipytent#_vimCreateJob'](command)
    elif bool(int(vim.eval('exists("*jobstart")'))):  # Neovim
        def __create_job_object(self, command):
            callback = FN['omnipytent#_nvimJobCallback']
            return FN.jobstart(command, dict(
                on_stdout=callback,
                on_stderr=callback,
                on_exit=callback,
            ))

    def handle_text_output(self, channel, data):
        buf = self._buffers[channel]
        if not data:
            return
        buf[-1] += data[0]
        buf.extend(data[1:])

    def _channel_output(self, channel):
        return '\n'.join(self._buffers[channel])

    @property
    def out(self):
        return self._channel_output('stdout')

    @property
    def err(self):
        return self._channel_output('stderr')

    def _resolve_returned_value(self, returned_value):
        return self

    def handle_exit(self, returncode):
        self.returncode = returncode
        self.run_next_frame('resume')
