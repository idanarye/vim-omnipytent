from .base import Base


class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'omnipytent'
        self.kind = 'omnipytent'

    def gather_candidates(self, context):
        return self.vim.eval('%s.call("get_source")' % context['yielded_command'])
