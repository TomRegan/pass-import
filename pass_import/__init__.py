# -*- encoding: utf-8 -*-
# pass import - Passwords importer swiss army knife
# Copyright (C) 2017-2020 Alexandre PUJOL <alexandre@pujol.io>.
#
"""Passwords importer swiss army knife."""

from collections import defaultdict, OrderedDict

import pass_import.decrypters  # noqa
import pass_import.formats  # noqa
import pass_import.managers  # noqa

from pass_import.__about__ import (__author__, __copyright__, __email__,
                                   __license__, __summary__, __title__,
                                   __uri__, __version__)
from pass_import.core import get_managers, get_detecters, Cap

__all__ = [
    '__title__', '__summary__', '__uri__', '__version__', '__author__',
    '__email__', '__license__', '__copyright__'
]


class ManagerError(Exception):
    """Errors related to managers' management. Most likely a bug if raised."""


class Managers(set):
    """Provide an interface to manage the managers' classes easily."""

    def __init__(self):
        super(Managers, self).__init__(get_managers())

    def classes(self, cap=Cap.IMPORT, frmt=None):
        """Generate the classes of pm with capabilities and format."""
        ignore = {'csv'}
        for pm in self:
            if cap in pm.cap:
                if frmt:
                    if pm.name in ignore:
                        continue
                    if pm.format == frmt:
                        yield pm
                else:
                    yield pm

    def get(self, name, frmt='', version='', cap=Cap.IMPORT):
        """Return a manager class from its classname or its format."""
        default = None
        for pm in self.classes(cap):
            # If name is a classname, return the class
            if pm.__name__ == name:
                return pm

            # If name is a password manager name, check its metadata
            if pm.name == name:
                if not default:
                    default = pm
                if pm.format == frmt and pm.version == version:
                    return pm

        if default:
            return default
        raise ManagerError('Unknown password manager: %s' % name)

    def names(self, cap=Cap.IMPORT):
        """Return the sorted list of password managers name."""
        names = set()
        for pm in self.classes(cap):
            names.add(pm.name)
        return sorted(names)

    def matrix(self, cap=Cap.IMPORT):
        """Return a dict of supported managers classes for all names."""
        matrix = defaultdict(list)
        for pm in self.classes(cap):
            matrix[pm.name].append(pm)
        return matrix


class Detecters(OrderedDict):
    """An ordered dictionary of the password managers format supported.

    This format dictionary is ordered to take care of the following
    requirements:

    - Most format common first
    - Parent format first. Eg: ``XML`` before ``HTML``,
      ``JSON`` before ``YAML``...

    """
    orders = {
        Cap.FORMAT: [
            'csv', 'xml', 'json', 'kdbx', 'yaml', '1pif', 'html', 'keychain'
        ],
        Cap.DECRYPT: []
    }

    def __init__(self, cap=Cap.FORMAT):
        self.cap = cap
        if self.cap not in Cap.FORMAT | Cap.DECRYPT:
            raise ManagerError('Capability not supported')

        cls = get_detecters()
        detecters = OrderedDict()
        for frmt in self.orders[cap]:
            for pm in cls:
                if pm.format == frmt and cap in pm.cap:
                    detecters[pm.format] = pm

        for pm in cls:
            if pm.format not in self.orders[cap] and cap in pm.cap:
                detecters[pm.format] = pm
        super(Detecters, self).__init__(detecters)
