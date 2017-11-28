import sys
from types import ModuleType
import imp

import vim

# In case this file gets reloaded
modules_to_remove = [importer for importer in sys.meta_path
                     if getattr(importer, '__module__', None) == __name__]
for module in modules_to_remove:
    sys.meta_path.remove(module)


class __Importer(object):
    module = ModuleType('omnipytent.ext')
    module.__path__ = [module.__name__]
    prefix = module.__name__ + '.'

    def find_module(self, fullname, path):
        if fullname == 'omnipytent.ext.omnipytent':
            # That's not omnipytent's path!
            return None
        if fullname == self.module.__name__:
            return self
        if path == [self.module.__name__]:
            return self

    def load_module(self, fullname):
        if fullname == self.module.__name__:
            return sys.modules.setdefault(fullname, self.module)

        assert fullname.startswith(self.prefix)
        name = fullname[len(self.prefix):]

        try:
            return sys.modules[fullname]
        except KeyError:
            pass

        module_path = vim.eval("globpath(&runtimepath, 'omnipytent/%s.py', 1, 1, 1)" % name)
        if not module_path:
            raise ImportError('No Omnipytent extension named %r' % name)
        if 1 < len(module_path):
            raise ImportError('Multiple Omnipytent extensions named %r' % name)
        module_path, = module_path

        submodule = imp.load_source(fullname, module_path)

        sys.modules[fullname] = submodule

        return submodule


sys.meta_path.append(__Importer())
