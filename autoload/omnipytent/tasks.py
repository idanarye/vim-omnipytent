from context import InvocationContext


class Task:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.dependencies = []
        self.send_context = False

    def invoke(self, ctx, *args):
        if self.send_context:
            self.func(ctx, *args)
        else:
            self.func(*args)

    def __repr__(self):
        return '<Task: %s>' % self.name


def invoke_with_dependencies(task, args):
    ctx = InvocationContext()

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
            task.invoke(ctx.for_task(task), *args)

