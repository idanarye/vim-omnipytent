from functools import partial

from .task_maker import TaskMaker


class CombineSources(TaskMaker):
    _is_maker_ = True

    from .tasks import OptionsTask as TaskType

    def __init__(self, sources):
        self.sources = sources

    def set_sources(self, *sources):
        self.sources = sources

    def all_dependencies(self, tasks_file):
        for source in self.sources:
            for dependency in source.all_dependencies(tasks_file):
                yield dependency

    def modify_task(self, task):
        task.set_sources = self.set_sources
        task.all_dependencies = self.all_dependencies

    def __call__(self, ctx):
        def redirector(target, inp):
            source_ctx, value = inp
            func = getattr(source_ctx, target)
            if target == '_preview' and func is None:
                return 'No preview for %s' % source.name
            return func(value)

        ctx.key(partial(redirector, '_key'))
        ctx.value(partial(redirector, '_value'))

        has_preview = False
        for source in self.sources:
            source_ctx = ctx._parent.for_task(source)
            for value in (source._resolve_options(source_ctx).values()):
                yield source_ctx, value
            has_preview = has_preview or bool(source_ctx._preview)

        if has_preview:
            ctx.preview(partial(redirector, '_preview'))


class CombineSourcesMulti(CombineSources):
    _is_maker_ = True
    from omnipytent.tasks import OptionsTaskMulti as TaskType
