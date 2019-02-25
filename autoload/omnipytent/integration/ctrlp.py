from collections import OrderedDict

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN


class CTRLP(SelectionUI):
    def on_yield(self):
        FN['ctrlp#omnipytent#start'](self.vim_obj)

    def gen_entry(self, i, item):
        return self.fmt(item)

    @property
    def _by_fmt(self):
        try:
            return self.__by_fmt
        except AttributeError:
            pass

        by_fmt = OrderedDict()

        for entry in self.source:
            base_fmt = self.fmt(entry)
            fmt = base_fmt
            num = 1
            while fmt in by_fmt:
                num += 1
                fmt = '%s (%s)' % (base_fmt, num)
            by_fmt[fmt] = entry

        self.__by_fmt = by_fmt
        return self.__by_fmt

    def get_source(self):
        return list(self._by_fmt.keys())

    def finish(self, choice):
        choice = self._by_fmt[choice]
        if self.multi:
            choice = [choice]
        self.resume(choice)
