from ..kind.openable import Kind as Openable


class Kind(Openable):
    def __init__(self, vim):
        super(Kind, self).__init__(vim)
        self.name = 'omnipytent-choice'

    def action_open(self, context):
        targets = context['targets']
        self.vim.command('call %s.call("finish", %r)' % (context['yielded_command'], [t['idx'] for t in targets]))
