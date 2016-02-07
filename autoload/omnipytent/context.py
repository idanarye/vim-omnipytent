
class InvocationContext:
    def __init__(self):
        self.dep_data = {}

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

