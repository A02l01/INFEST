#!/usr/bin/env python3

__names__ = ["data_gmax", "data_atha", "data_marca"]


def resource_filename(module: str, resource: str) -> str:
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


gmax_dir = resource_filename(__name__, "gmax")
atha_dir = resource_filename(__name__, "atha")
marca_dir = resource_filename(__name__, "marca")
