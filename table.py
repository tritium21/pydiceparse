import collections.abc
import pathlib
import random

import pickledb


class TableRoller(collections.abc.MutableMapping):
    def __init__(self, db_path):
        self.db_path = pathlib.Path(db_path).resolve()
        self.db = pickledb.load(self.db_path, True)

    def create(self, name, data):
        if isinstance(data, str):
            data = [d.strip() for d in data.split('\n')]
        self.db.set(name, data)

    update = create

    def read(self, name):
        return self.db.get(name)

    def delete(self, name):
        self.db.rem(name)

    def list(self):
        return list(self.db.getall())

    def roll(self, name, count=1, rng=random):
        return rng.choices(self.read(name), k=count)

    def __getitem__(self, key):
        return self.read(key)

    def __setitem__(self, key, value):
        self.create(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def __iter__(self):
        return iter(self.db)

    def __len__(self):
        return len(self.db)

    def __contains__(self, x):
        return x in self.db