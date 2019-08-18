import yaml


class Config(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.load_config_file()

    def load_config_file(self):
        with open(self.filepath, 'rb') as config:
            c = yaml.safe_load(config)

        for key in c.keys():
            self.__setattr__(key, c[key])
