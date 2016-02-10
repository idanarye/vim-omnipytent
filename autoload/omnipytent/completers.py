import os
import glob


def __generate_path_completer(root, dirs_only):
    def completer(parts):
        dirpath, filename = os.path.split(parts[-1])
        basedir = os.path.join(root, dirpath)
        filename = filename.replace('[', '[[]')
        filename = filename.replace('*', '[*]')
        filename = filename.replace('?', '[?]')
        glob_target = os.path.join(basedir, '%s*' % filename)
        if dirs_only:
            glob_target = os.path.join(glob_target, '')
        for path in glob.glob(glob_target):
            path = os.path.relpath(path, root)
            if dirs_only:
                path = os.path.join(path, '')
            yield path

    return completer


def file_completer(root=''):
    return __generate_path_completer(root=root, dirs_only=False)


def dir_completer(root=''):
    return __generate_path_completer(root=root, dirs_only=True)

