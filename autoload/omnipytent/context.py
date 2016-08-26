import re


class InvocationContext:
    def __init__(self, task_file, main_task):
        self.dep_data = {}
        self.task_file = task_file
        self.main_task = main_task

    def for_task(self, task):
        return TaskContext(self, task)


class TaskContext:
    def __init__(self, parent, task):
        self.parent = parent
        self.task = task
        self.dep = DepDataFetcher(self)

    def __repr__(self):
        return '<TaskContext: %s>' % self.task.name

    def pass_data(self, data):
        self.parent.dep_data[self.task] = data

    @property
    def cache(self):
        try:
            return self.parent.task_file.tasks_cache[self.task.name]
        except KeyError:
            return self.parent.task_file.tasks_cache.setdefault(self.task.name, TaskCache())

    @property
    def is_main(self):
        return self.parent.main_task == self.task


class TaskCache:
    pass


class DepDataFetcher:
    def __init__(self, task_context):
        self.__task_context = task_context

    def __getattr__(self, name):
        for dependency in self.__task_context.task.dependencies:
            if dependency.name == name:
                try:
                    return self.__task_context.parent.dep_data[dependency]
                except KeyError:
                    raise AttributeError('%s did not pass data' % dependency)
        raise AttributeError('%s has no dependency named "%s"' % (self.__task_context.task, name))


class CompletionContext:
    @classmethod
    def from_vim_completion_args(cls, tasks_file, arg_lead, cmd_line, cursor_pos):
        cmd_line_before_cursor = cmd_line[:cursor_pos]
        parts = re.findall(r'(?:[^\\\s]|(?:\\\\)|(?:\\\s))+', cmd_line_before_cursor)
        if cmd_line_before_cursor.endswith(' '):
            parts.append('')

        assert 2 <= len(parts)
        if len(parts) == 2:  # task name completion
            return cls(task=None,
                       arg_index=None,
                       arg_prefix=parts[1],
                       cmd_line=cmd_line,
                       cursor_pos=cursor_pos)
        else:
            return cls(task=tasks_file[parts[1]],
                       arg_index=len(parts) - 3,
                       arg_prefix=parts[-1],
                       cmd_line=cmd_line,
                       cursor_pos=cursor_pos)

    def __init__(self, task, arg_index, arg_prefix, cmd_line, cursor_pos):
        self.task = task
        self.arg_index = arg_index
        self.arg_prefix = arg_prefix
        self.cmd_line = cmd_line
        self.cursor_pos = cursor_pos

    @property
    def arg_name(self):
        if self.arg_index is None:
            return None
        else:
            assert 0 <= self.arg_index
            try:
                return self.task._task_args[self.arg_index]
            except IndexError:
                return self.task._task_varargs  # may be None - but that just means the argument is None

