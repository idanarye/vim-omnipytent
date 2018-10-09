import vim

from omnipytent.async_execution import AsyncCommand
from omnipytent.execution import FN, quote
from omnipytent.util import vim_repr, RawVim


class FZF(AsyncCommand):
    def __init__(self, source, multi=False, prompt=None):
        self.source = list(source)
        self.multi = multi
        self.prompt = prompt

    def on_yield(self):
        params = {}
        params['source'] = list(map(str, self.source))

        sink = RawVim("function('omnipytent#_redirectToNotify')")
        flags = []
        if self.multi:
            params['sink*'] = sink
            flags.append('--multi')
        else:
            params['sink'] = sink
        params['yieldedCommand'] = self.vim_obj
        params['notifyMethod'] = 'choose'

        params['down'] = '~40%'
        if self.prompt:
            flags.append('--prompt ' + quote(self.prompt))

        params['options'] = ' '.join(map(str, flags))
        FN['fzf#run'](params)

    def choose(self, choice):
        self.resume(choice)
