from types import ModuleType
import sys


class OmnipytentExtension(ModuleType):
    __all__ = ()
    __package__ = __name__
    __path__ = []
    __file__ = __file__


    # def __dir__(self):
        # return ['foo']

    def __getattr__(self, name):
        print('yo')
        # can't be done at file's top level for some reason...
        import imp
        import vim

        module_path = vim.eval("globpath(&runtimepath, 'omnipytent/%s.py', 1, 1, 1)" % name)
        if not module_path:
            print("globpath(&runtimepath, 'omnipytent/%s.py', 1, 1, 1)" % name)
            print(self)
            return object.__getattr__(self, name)
            import traceback
            traceback.print_stack()
            from types import ModuleType
            # return ModuleType.__getattribute__(self, name)
            return ModuleType.__path__
            # return getattr(super(ModuleType, self), name)
            # return module_path
            # raise ImportError
            # from types import ModuleType
            # print(super(ModuleType, self))
            # print(dir(super(ModuleType, self)))
            # import traceback
            # try:
                # return getattr(super(ModuleType, self), name)
            # except:
                # print('hi', name, traceback.print_stack())
            # raise ImportError('No Omnipytent extension module named %r' % name)
        try:
            module_path, = module_path
        except ValueError:
            raise ImportError('Multiple Omnipytent extension modules named %r: %s' % (name, module_path))

        print('hi')
        return imp.load_source('%s.%s' % (self.__name__, name), module_path)

    # def __dir__(self):
        # return ['foo']


ext = OmnipytentExtension('omnipytent.ext')
sys.modules[ext.__name__] = ext
