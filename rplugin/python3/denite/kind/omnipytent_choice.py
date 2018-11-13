from ..kind.openable import Kind as Openable


class Kind(Openable):
    def __init__(self, vim):
        super(Kind, self).__init__(vim)
        self.name = 'omnipytent-choice'

    def action_open(self, context):
        targets = context['targets']
        self.vim.command('call %s.call("finish", %r)' % (context['yielded_command'], [t['idx'] for t in targets]))

    def action_preview(self, context):
        target = context['targets'][0]
        index = target['idx']

        path = self.vim.eval('%s.call("create_preview_file", %s)' % (context['yielded_command'], target['idx']))
        prev_id = self.vim.call('win_getid')

        self.vim.call('denite#helper#preview_file', context, path)
        self.vim.command('wincmd P')

        self.vim.call('win_gotoid', prev_id)
