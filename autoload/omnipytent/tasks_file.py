import vim
import sys
import os.path
import imp

from tasks import Task


class TasksFile:
    def __init__(self):
        self.filename = self.default_name()
        self.last_modified = None

    def open(self, on_task=None):
        vim.command('edit %s' % self.filename)
        if not os.path.exists(self.filename):
            vim.current.buffer[:] = ['import vim',
                                     'from omnipytent import task, ctask',
                                     '']
            if on_task:
                self._create_task_in_current_buffer(on_task)
            else:
                vim.command(str(len(vim.current.buffer)))
        else:
            if on_task:
                if self.is_stale:
                    self.load()
                try:
                    task = self.tasks[on_task]
                    line = task.func.func_code.co_firstlineno
                    vim.command('edit %s' % self.filename)
                    vim.command(str(line))
                except KeyError:
                    self._create_task_in_current_buffer(on_task)

    def _create_task_in_current_buffer(self, taskname):
        last_line = len(vim.current.buffer) - 1
        while 0 < last_line and not vim.current.buffer[last_line].strip():
            last_line -= 1
        vim.current.buffer[last_line + 1:] = ['', '', '@task', 'def %s():' % taskname, '    ', '']
        vim.command(str(len(vim.current.buffer) - 1))
        vim.command('startinsert!')

    def load(self):
        self.tasks = {}
        self.module = imp.load_source('_omnypytent_tasksfile', self.filename)
        for ident, value in self.module.__dict__.iteritems():
            if isinstance(value, Task):
                self.tasks[ident] = value
        self.last_modified = os.path.getmtime(self.filename)

    def __getitem__(self, key):
        return self.tasks[key]

    @staticmethod
    def default_name():
        try:
            return '%s.omnipytent.%s.py' % (vim.vars['omnipytent_filePrefix'], sys.version_info.major)
        except KeyError:
            raise Exception('g:omnipytent_filePrefix not set')

    @property
    def is_stale(self):
        try:
            return self.last_modified != os.path.getmtime(self.filename)
        except OSError:
            return True

    def load_if_stale(self):
        if self.is_stale:
            self.load()


__last_tasks_file = [None]


def get_tasks_file():
    if __last_tasks_file[0] is None:
        __last_tasks_file[0] = TasksFile()
    return __last_tasks_file[0]

