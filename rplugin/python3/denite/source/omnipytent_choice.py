from .base import Base


class Source(Base):
    def __init__(self, vim):
        super(Source, self).__init__(vim)
        self.name = 'omnipytent-choice'
        self.kind = 'omnipytent-choice'

    def gather_candidates(self, context):
        return self.vim.eval('%s.call("get_source")' % context['yielded_command'])
