import abc

from context import InvocationContext


class Task:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.dependencies = []

    def invoke(self, ctx, *args):
        self.func(ctx.for_task(self), *args)

    def __repr__(self):
        return '<Task: %s>' % self.name

    @classmethod
    def _dsl(cls, *args):
        if len(args) == 1 and args[0].__class__ == abc.types.FunctionType:
            return cls(args[0])

        def wrapper(func):
            result = cls(func)

            for arg in args:
                if isinstance(arg, Task) or isinstance(arg, str):
                    result.dependencies.append(arg)

            return result

        return wrapper


def invoke_with_dependencies(tasks_file, task, args):
    ctx = InvocationContext(tasks_file, task)

    stack = [task]
    run_order = []
    while stack:
        popped_task = stack.pop()
        run_order.insert(0, popped_task)
        stack += popped_task.dependencies

    already_invoked = set()
    for task in run_order:
        if task not in already_invoked:
            already_invoked.add(task)
            task.invoke(ctx, *args)

