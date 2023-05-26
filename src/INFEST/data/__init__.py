#!/usr/bin/env python3


def resource_filename(module, resource):
    """ Emulates the behaviour of the old setuptools resource_filename command.

    Basically it just gets rid of the context manager thing, because it's not
    needed. None of the files are zip files or create any temporary files
    that need to be cleaned up.

    This function would be unsafe to use with anything that will be extracted.
    """

    from importlib.resources import path
    with path(module, resource) as handler:
        filename = str(handler)

    return filename


def data_gmax():
    from os import listdir
    from os.path import join
    dir = resource_filename(__name__, "gmax")
    return [join(dir, f) for f in listdir(dir)]
