import os
import json

from exceptions import AntennyConfigException


CONFIGS = "configs"
DEFAULTS = "/configs/defaults.json"


class Config:
    def __init__(self, config_type="antenny"):
        self.config_type = config_type
        self._config = None
        self._config_name = self._get_default_config()
        self.load(self._config_name)

    @staticmethod
    def _check_name(config_name):
        """
        Checks the config name for special rules
        :param config_name:
        :return:
        """
        if "/" in config_name or "\\" in config_name:
            print("Config name can not look like a unix path")
            return False
        if "_help" in config_name:
            print("Config name is invalid, \"_help\" is reserved")
            return False
        return True

    def _get_default_config(self):
        """
        Gets the default config form the meta config
        :return:
        """
        with open(DEFAULTS, "r") as fh:
            return json.load(fh)[self.config_type]

    def _get_original_default_config(self):
        """
        Gets the stock default config from the meta config
        :return:
        """
        with open(DEFAULTS, "r") as fh:
            return json.load(fh)["original_{}".format(self.config_type)]

    def _get_type_path(self):
        """
        Gets the proper config dir path based on type
        :return:
        """
        return "/{}/{}".format(CONFIGS, self.config_type)

    def _get_config_path(self, config_name):
        """
        Gets the path of the config specified
        :param config_name:
        :return:
        """
        return "{}/{}.json".format(self._get_type_path(), config_name)

    def _get_this_config_path(self):
        """
        Gets the current config path
        :return:
        """
        return self._get_config_path(self._config_name)

    def _list_configs(self):
        """
        Lists all available configs
        :return:
        """
        configs = os.listdir(self._get_type_path())
        config_names = list()
        for config in configs:
            if "_help" not in config:
                config = config.split(".")[0]
                config_names.append(config)
        return config_names

    def _is_config(self, name: str = None):
        """
        Checks if the specified config exists
        :param name:
        :return:
        """
        configs = self._list_configs()
        return name in configs

    def _get_help_path(self):
        """
        Gets the help config path
        :return:
        """
        return self._get_config_path(self._config_name + "_help")

    def load(self, name: str = None):
        """
        Load a new existing config
        :param name:
        :return:
        """
        if name is not None:
            if not self._check_name(name):
                print("Failed to load {} due to invalid name".format(name))
                return False
            if not self._is_config(name):
                print("Failed to load {}, config does not exist".format(name))
                return False
            self._config_name = name

        with open(self._get_this_config_path(), "r") as fh:
            try:
                self._config = json.load(fh)
            except ValueError:
                print("JSON parse error %s" % (self._get_this_config_path()))

    def save(self, name: str = None, force=False):
        """
        Saves the config to a file
        :param name:
        :param force: overwrite an existing config
        :return:
        """
        if name is not None and name != self._config_name:
            if not self._check_name(name):
                print("Failed to save config as {} due to invalid name".format(name))
                return False
            if self._is_config(name) and not force:
                print("The config {} already exists, use \"force\" option to overwrite")
                return False
            elif force:
                print("Overwriting the config {}".format(name))
            self._config_name = name
        with open(self._get_this_config_path(), "w") as fh:
            json.dump(self._config, fh)
        return self._config_name

    def set(self, key, value):
        """
        Set a config value
        :param key:
        :param value:
        :return:
        """
        if self._config is None:
            print("Trying to set key: {} to value: {} in an empty config".format(key, value))
            raise AntennyConfigException("Trying to set key: {} to value: {} in an empty config".format(key, value))
        self._config[key] = value
        return True

    def get(self, key):
        """
        Get a config value
        :param key:
        :return:
        """
        if self._config is None:
            print("Trying to get key: {} in an empty config".format(key))
            raise AntennyConfigException("Trying to get key: {} in an empty config".format(key))
        if key not in self._config:
            print("The key {} does not exists in the current config".format(key))
            raise AntennyConfigException("The key {} does not exists in the current config".format(key))
        return self._config[key]

    def print_values(self):
        """
        Print all config key/value pairs
        :return:
        """
        if self._config is None:
            print("Trying to print key value pairs from an empty config")
            return False
        for key, value in self._config.items():
            print("{}: {}".format(key, json.dumps(value)))
        return True

    def print_keys(self):
        """
        Print all config keys
        :return:
        """
        if self._config is None:
            print("Trying to print keys from an empty config")
            return False
        for key in self._config:
            print(key)

    def save_as_default_config(self):
        """
        Saves the config as the default config on startup
        :return:
        """
        self.save()
        with open(DEFAULTS, "r") as fh:
            defaults = json.load(fh)
        defaults[self.config_type] = self._config_name
        with open(DEFAULTS, "w") as fh:
            json.dump(defaults, fh)

    def load_default_config(self):
        """
        Reloads the default config
        :return:
        """
        return self.load(self._get_default_config())

    def reset_default_config(self):
        """
        Resets the default config to the stock
        :return:
        """
        return self.load(self._get_original_default_config())

    def new_config(self, config_name):
        """
        Change the current config name
        :param config_name:
        :return:
        """
        self._config_name = config_name

    def check(self):
        """
        Checks that the config is not missing keys based on the stock config
        :return:
        """
        check_flag = True
        with open(DEFAULTS, "r") as fh:
            valid_config_path = self._get_config_path(json.load(fh)["original_{}".format(self.config_type)])
        with open(valid_config_path, "r") as fh:
            valid_config = json.load(fh)
        for key in valid_config:
            if key not in self._config:
                print("The config {} is missing the key {}".format(self.get_name(), key))
                check_flag = False
        return check_flag

    def get_name(self):
        """
        Gets the config name
        :return:
        """
        return self._config_name

    def get_help_info(self):
        """
        Gets the help info if available
        :return:
        """
        with open(self._get_help_path(), "r") as fh:
            return json.load(fh)

    def list_configs(self):
        """
        Gets a list of all available configs
        :return:
        """
        configs = list()
        for config in self._list_configs():
            if config == self._config_name:
                config = "> " + config
            configs.append(config)
        return configs

    def get_config(self):
        """
        Gets the config as a dictionary
        :return:
        """
        return self._config
