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
        if on_task:
            raise NotImplementedError()
        vim.command('edit %s' % self.filename)

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
        return self.last_modified != os.path.getmtime(self.filename)


__last_tasks_file = [None]


def get_tasks_file():
    if __last_tasks_file[0] is None:
        __last_tasks_file[0] = TasksFile()
    return __last_tasks_file[0]

