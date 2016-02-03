
from .tasks import Task

def task(func):
    return Task(func)

