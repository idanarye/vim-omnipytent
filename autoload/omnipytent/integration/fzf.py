import vim

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN, quote
from omnipytent.util import RawVim

class FZF(SelectionUI):
    def gen_entry(self, i, item):
        return '%s %s' % (i, self.fmt(item))

    def on_yield(self):
        params = {}
        params['source'] = self.get_source()

        sink = RawVim("function('omnipytent#integration#fzf#finish')")
        flags = []
        flags.append('--with-nth=2..')
        if self.multi:
            params['sink*'] = sink
            flags.append('--multi')
        else:
            params['sink'] = sink
        params['yieldedCommand'] = self.vim_obj

        params['down'] = '~40%'
        if self.prompt:
            flags.append('--prompt ' + quote(self.prompt))

        params['options'] = ' '.join(map(str, flags))
        FN['fzf#run'](params)

    def finish(self, choice):
        self.run_next_frame('finish_indices', choice)
