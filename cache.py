import pickle

class Cache:
    def __init__(self):
        self.data = {}

    def add(self, key, item):
        self.data[key] = item

    def get(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None

    def size(self):
        return len(self.data)

    @staticmethod
    def save(obj, filename):
        fd = open(filename, 'w')
        pickle.dump(obj, fd)

    @staticmethod
    def load(filename):
        fd = open(filename, 'r')
        return pickle.load(fd)


