
class Task:
    def __init__(self, func):
        self.func = func

    def invoke(self, ctx, *args):
        self.func(*args)

