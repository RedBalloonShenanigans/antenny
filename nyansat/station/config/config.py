from exceptions import AntennyConfigException

try:
    import ujson as json
except ImportError:
    import json
import os


CONFIGS = "/configs/"
ANTENNY_CONFIGS_PATH = CONFIGS + "antenny_configs/"
DEFAULTS = CONFIGS + "defaults.json"

class Config:
    def __init__(self):
        self._config = None
        self._config_name = self._get_default_config()
        self.load(self._config_name)

    @staticmethod
    def _get_default_config():
        with open(DEFAULTS, "r") as fh:
            return json.load(fh)["config"]

    @staticmethod
    def _get_original_default_config():
        with open(DEFAULTS, "r") as fh:
            return json.load(fh)["original_config"]

    @staticmethod
    def _get_path(config_name):
        return ANTENNY_CONFIGS_PATH + config_name + ".json"

    @staticmethod
    def _list_configs():
        configs = os.listdir(ANTENNY_CONFIGS_PATH)
        config_names = list()
        for config in configs:
            if "_help" not in config:
                config = config.split(".")[0]
                config_names.append(config)
        return config_names

    @staticmethod
    def _check_name(config_name):
        if "/" in config_name or "\\" in config_name:
            print("Config name can not look like a unix path")
            return False
        if "_help" in config_name:
            print("Config name is invalid, \"_help\" is reserved")
            return False
        return True

    def _is_config(self, config_name):
        configs = self._list_configs()
        return config_name  in configs

    def _get_current_path(self):
        return self._get_path(self._config_name)

    def _get_help_path(self):
        return self._get_path(self._config_name + "_help")

    def load(self, config_name):
        if not self._check_name(config_name):
            print("Failed to load {} due to invalid name".format(config_name))
            return False
        if not self._is_config(config_name):
            print("Failed to load {}, config does not exist".format(config_name))
            return False
        self._config_name = config_name
        with open(self._get_current_path(), "r") as fh:
            self._config = json.load(fh)

    def save_as(self, config_name, force=False):
        if not self._check_name(config_name):
            print("Failed to save config as {} due to invalid name".format(config_name))
            return False
        if self._is_config(config_name) and not force:
            print("The config {} already exists, use \"force\" option to overwrite")
            return False
        elif force:
            print("Overwriting the config {}".format(config_name))
        self._config_name = config_name
        with open(self._get_current_path(), "w") as fh:
            json.dump(self._config, fh)
        return self._config_name

    def save(self):
        self.save_as(self._config_name, force=True)

    def set(self, key, value):
        if self._config is None:
            print("Trying to set key: {} to value: {} in an empty config".format(key, value))
            raise AntennyConfigException("Trying to set key: {} to value: {} in an empty config".format(key, value))
        self._config[key] = value
        return True

    def get(self, key):
        if self._config is None:
            print("Trying to get key: {} in an empty config".format(key))
            raise AntennyConfigException("Trying to get key: {} in an empty config".format(key))
        if key not in self._config:
            print("The key {} does not exists in the current config".format(key))
            raise AntennyConfigException("The key {} does not exists in the current config".format(key))
        return self._config[key]

    def print_values(self):
        if self._config is None:
            print("Trying to print key value pairs from an empty config")
            return False
        for key, value in self._config.items():
            print("{}: {}".format(key, json.dumps(value)))
        return True

    def print_keys(self):
        if self._config is None:
            print("Trying to print keys from an empty config")
            return False
        for key in self._config:
            print()

    def save_as_default_config(self):
        self.save()
        with open(DEFAULTS, "r") as fh:
            defaults = json.load(fh)
        defaults["config"] = self._config_name
        with open(DEFAULTS, "w") as fh:
            json.dump(defaults, fh)

    def load_default_config(self):
        return self.load(self._get_default_config())

    def reset_default_config(self):
        return self.load(self._get_original_default_config())

    def new_config(self, config_name):
        self._config_name = config_name

    def check(self):
        check_flag = True
        with open(DEFAULTS, "r") as fh:
            valid_config_path = self._get_path(json.load(fh)["original_config"])
        with open(valid_config_path, "r") as fh:
            valid_config = json.load(fh)
        for key in valid_config:
            if key not in self._config:
                print("The config {} is missing the key {}".format(self.get_name(), key))
                check_flag = False
        return check_flag

    def get_name(self):
        return self._config_name

    def get_help_info(self):
        with open(self._get_help_path(), "r") as fh:
            return json.load(fh)

    def list_configs(self):
        configs = list()
        for config in self._list_configs():
            if config == self._config_name:
                config = "> " + config
            configs.append(config)
        return configs
