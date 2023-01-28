import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskmn import __app_name__, __version__, task_manager_cli, config

runner = CliRunner()
test_store_location = Path("test_init_store.csv")
CONFIG_LOCATION = config.CONFIG_FILE_PATH
TEST_CONFIG_LOCATION = Path(str(CONFIG_LOCATION) + ".new")


def _add_tasks_via_cli_and_test_success(addset):
    for num, addition in enumerate(addset):
        num += 1
        cli = runner.invoke(task_manager_cli.app, ["add"] + addition)
        assert cli.exit_code == 0
        if num % 2 == 0:
            cli = runner.invoke(task_manager_cli.app, ["complete", str(num)])
            assert cli.exit_code == 0


def _complete_task(index):
    cli = runner.invoke(task_manager_cli.app, ["complete", str(index)])
    return cli


class TestCli:
    #  Two Past due, Three Not yet due, #Every odd task will be completed, so 3 completed 3 not
    ADD_ARGUMENTS = [["Name"],
                     ["Name2", "-dl", "2020-10-23"],
                     ["Name3", "-dl", "2021-12-07"],
                     ["Name4", "-dl", "2024-10-23"],
                     ["Name5", "-dl", "2026-12-07"],
                     ["Name6", "-dl", "2028-12-07"]
                     ]
    test_store_location = Path()

    @pytest.fixture
    def test_environment(self, tmp_path):
        """
        Should run the init command, save the previous state, and then restore the original environment after the test
        :return:
        """
        global test_store_location
        original = False
        if CONFIG_LOCATION.exists():
            original = True
            shutil.copy(CONFIG_LOCATION, TEST_CONFIG_LOCATION)  # Copy any existing data to a temporary file
        self.test_store_location = tmp_path / test_store_location
        cli = runner.invoke(task_manager_cli.app, ["init", "-s", str(self.test_store_location)])
        yield cli

        if original:
            shutil.copy(TEST_CONFIG_LOCATION, CONFIG_LOCATION)  # Copy original data back to the test dir
            os.remove(TEST_CONFIG_LOCATION)  # Remove test data
        else:
            os.remove(CONFIG_LOCATION)  # If no config exists originally just remove the file
        os.remove(self.test_store_location)  # remove the test store location

    def _get_lines_from_file(self):
        with open(self.test_store_location, 'r') as file:
            data = [line.rstrip() for line in file]
            length = len(data)
        return length - 1, data[1:]  # Ignore the Header Line

    def test_version(self):
        """
        Test passes if the result of -v and --version print the correct info
        :return:
        """
        result = runner.invoke(task_manager_cli.app, ["--version"])
        assert result.exit_code == 0
        assert f"{__app_name__} v{__version__}\n" in result.stdout
        result = runner.invoke(task_manager_cli.app, ["-v"])
        assert result.exit_code == 0
        assert f"{__app_name__} v{__version__}\n" in result.stdout

    def test_init_cli(self, test_environment):
        """
        Will pass if a store and a configuration file exists after init is run
        :return:
        """
        cli = test_environment
        assert cli.exit_code == 0

        assert CONFIG_LOCATION.exists()  # Check if the created paths exist
        assert self.test_store_location.exists()

    def test_add_cli(self, test_environment):
        """
        Will add Tasks via cli
        :param test_environment:
        :return:
        """

        cli = test_environment
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 0

        cli = runner.invoke(task_manager_cli.app, ["add", "Name"])
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 1

        cli = runner.invoke(task_manager_cli.app, ["add", "Name"])
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 2

    @pytest.mark.parametrize(
        "argument, value, index",
        [
            pytest.param("-n", "Edited_Name", 1),
            pytest.param("-desc", "Description", 2),
            pytest.param("-p", "2", 4),
            pytest.param("-dl", "2020-01-23 00:00:00", 3)
        ],
    )
    def test_edit_cli(self, test_environment, argument, value, index):
        """
        Will edit Tasks via cli
        :param test_environment:
        :return:
        """

        cli = test_environment
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 0

        _add_tasks_via_cli_and_test_success(self.ADD_ARGUMENTS)

        cli = runner.invoke(task_manager_cli.app, ["edit", "1", "-f", argument, value])
        assert cli.exit_code == 0
        length, data = self._get_lines_from_file()
        assert length == len(self.ADD_ARGUMENTS)
        data_list = data[0].strip().split(",")
        print(data_list)
        assert data_list[index] == value

    def test_complete_cli(self, test_environment):
        """
        Will edit Tasks via cli
        :param test_environment:
        :return:
        """

        cli = test_environment
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 0

        _add_tasks_via_cli_and_test_success(self.ADD_ARGUMENTS)

        length, data = self._get_lines_from_file()
        assert length == len(self.ADD_ARGUMENTS)
        data_list = data[0].strip().split(",")
        print(data_list)
        assert data_list[6] == "0"

        cli = _complete_task(1)
        assert cli.exit_code == 0
        length, data = self._get_lines_from_file()
        assert length == len(self.ADD_ARGUMENTS)
        data_list = data[0].strip().split(",")
        print(data_list)
        assert data_list[6] == "1"

        cli = _complete_task(1)
        assert cli.exit_code == 0
        length, data = self._get_lines_from_file()
        assert length == len(self.ADD_ARGUMENTS)
        data_list = data[0].strip().split(",")
        print(data_list)
        assert data_list[6] == "0"

    @pytest.mark.parametrize(
        "argset, ending_length",
        [
            pytest.param([], 0),  # Default Clear Behaviour
            pytest.param(["-p"], 4),  # Clear Past due
            pytest.param(["-c"], 3),  # Clear Completed
            pytest.param(["-p", "-c"], 6)  # Invalid Input
        ],
    )
    def test_clear_cli(self, test_environment, argset, ending_length):
        """
        Will edit Tasks via cli
        :param test_environment:
        :return:
        """

        cli = test_environment
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 0

        _add_tasks_via_cli_and_test_success(self.ADD_ARGUMENTS)

        cli = runner.invoke(task_manager_cli.app, ["clear", "-f", *argset])

        if len(argset) < 2:  # Only one argument is allowed
            assert cli.exit_code == 0
        else:
            assert cli.exit_code == 1
        length, data = self._get_lines_from_file()
        assert length == ending_length
        print(data)

    @pytest.mark.parametrize(
        "addset, argset, ending_length",
        [
            pytest.param(ADD_ARGUMENTS, "1", 5),  # Default Clear Behaviour
            pytest.param(ADD_ARGUMENTS, "6", 5),  # Clear Past due
            pytest.param(ADD_ARGUMENTS, "0", 6),  # Clear Past due
            pytest.param(ADD_ARGUMENTS, "-15", 6),  # Clear Completed
            pytest.param(ADD_ARGUMENTS, "53", 6)  # Invalid Input
        ],
    )
    def test_delete_cli(self, test_environment, addset, argset, ending_length):
        """
        Will edit Tasks via cli
        :param test_environment:
        :return:
        """
        cli = test_environment
        assert cli.exit_code == 0
        assert self._get_lines_from_file()[0] == 0
        _add_tasks_via_cli_and_test_success(addset)

        cli = runner.invoke(task_manager_cli.app, ["delete", "-f", argset])

        if 0 < int(argset) <= len(self.ADD_ARGUMENTS):  # Task to delete must be within the range allowed
            assert cli.exit_code == 0
        else:
            assert cli.exit_code != 0
        length, data = self._get_lines_from_file()
        assert length == ending_length
        print(data)
