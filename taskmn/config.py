import configparser
import errno
import os
from pathlib import Path

import typer

from taskmn import __app_name__, data_store
from taskmn.exceptions import ConfigDirectoryError, ConfigFileError

"""
This modules defines the methods used to provide configuration of the app

Constants

CONFIG_DIR_PATH : Path
CONFIG_FILE_PATH: Path

Functions

init_app(Path)
_init_config_file()
_create_store(Path)
def modify_config_file(Path):

"""
CONFIG_DIR_PATH = Path(typer.get_app_dir(__app_name__))
CONFIG_FILE_PATH = CONFIG_DIR_PATH / "config.ini"
FILTERS_CONFIG_FILE_PATH = CONFIG_DIR_PATH / "filters.ini"



def init_app(store_path, exists=False):
    """
    Initializes the configuration file and Store
    :param exists: The specified path exists on the filesystem
    :param Path store_path: The path to the Store
    :raises ConfigFileError: Error creating the configuration file
    :raises ConfigDirectoryError: Error creating the configuration directory
    :raises ConfigFileError: Error writing to the configuration file
    """
    if exists:
        if not Path(store_path).exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), store_path)
    _init_config_file()
    _create_configs(store_path)


def _init_config_file():
    """
    Creates the configuration file for the app
    :raises ConfigFileError: Error creating the configuration file
    :raises ConfigDirectoryError: Error creating the configuration directory
    """
    try:
        CONFIG_DIR_PATH.mkdir(exist_ok=True)
    except OSError:
        raise ConfigDirectoryError(CONFIG_DIR_PATH)
    try:
        CONFIG_FILE_PATH.touch(exist_ok=True)
        FILTERS_CONFIG_FILE_PATH.touch(exist_ok=True)
    except OSError:
        raise ConfigFileError(CONFIG_FILE_PATH)


def _create_configs(data_path: Path):
    """
    Writes Store location to config file
    :param data_path: path to the data store
    :raises ConfigFileError: Error writing to the configuration file
    """
    data_path = os.path.abspath(data_path)

    config_parser = configparser.ConfigParser()
    config_parser["General"] = {"Storage": data_path}

    filter_config_parser = configparser.ConfigParser()
    default_filters = [
        {"name": "Past Due", "criteria": "task_deadline < DATETIME('now')"},
        {"name": "Not Due", "criteria": "task_deadline > DATETIME('now')"},
        {"name": "Completed", "criteria": "task_completed = TRUE"},
        {"name": "Not Completed", "criteria": "task_completed = False"},
        {"name": "No Tasks",
         "criteria": "SELECT COUNT(*) FROM tag LEFT JOIN tag_task ON tag.tag_id = tag_task.tag_id WHERE tag_task.tag_id IS NULL"}
    ]

    for idx, f in enumerate(default_filters):
        section_name = f"filter_{idx}"
        filter_config_parser[section_name] = f

    try:
        with CONFIG_FILE_PATH.open("w") as config_file:
            config_parser.write(config_file)
    except OSError:
        exp = ConfigFileError(CONFIG_FILE_PATH)
        exp.message = f'Writing to config file at "{exp.path}" has failed'
        raise exp

    try:
        with FILTERS_CONFIG_FILE_PATH.open("w") as config_file:
            filter_config_parser.write(config_file)
    except OSError:
        exp = ConfigFileError(FILTERS_CONFIG_FILE_PATH)
        exp.message = f'Writing to config file at "{exp.path}" has failed'
        raise exp


def modify_stored_path(store_path):
    """
    Changes the store path stored in the configuration file to the one provided
    :param store_path: Store path to change
    :raises ConfigFileError: Error writing to the configuration file
    :raises OSError: Error reading from the configuration file
    """
    if os.path.exists(CONFIG_FILE_PATH) is False:
        init_app(store_path)
    else:
        store_path = os.path.abspath(store_path)
        config_parser = configparser.ConfigParser()
        config_parser.read(CONFIG_FILE_PATH)
        xstore = config_parser["General"]["Storage"]

        config_parser["General"] = {"Storage": store_path, "XStorage": xstore}
        try:
            with CONFIG_FILE_PATH.open("w") as config_file:
                config_parser.write(config_file)
        except OSError:
            exp = ConfigFileError(CONFIG_FILE_PATH)
            exp.message = f'Writing to config file at "{exp.path}" has failed'
            raise exp
