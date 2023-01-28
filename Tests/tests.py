import csv
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskmn import __app_name__, __version__, task_manager_cli, task as TASK, task_manager, exceptions, config, \
    task_store

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


class TestManager:
    TASK_LIST = [
        TASK.Task.load_from_data("Name", "Description", "2064-03-03", 0, 1, "2011-01-26 21:21:47.813295", True),
        TASK.Task.load_from_data("Name2", "Description2", "2032-03-03", 1, 2, "2015-01-26 21:21:47.813295", True),
        TASK.Task.load_from_data("Name3", "Description3", "2016-03-03", 2, 3, "2004-01-26 21:21:47.813295", False),
        TASK.Task.load_from_data("Name4", "Description4", "2008-03-03", 1, 4, "2003-01-26 21:21:47.813295", False),
        TASK.Task.load_from_data("Name5", "Description5", "2004-03-03", 0, 5, "2002-01-26 21:21:47.813295", False),
        TASK.Task.load_from_data("Name6", "Description6", "2002-03-03", 1, 6, "2001-01-26 21:21:47.813295", True),
    ]
    TASK_SORT_RESULT_DICT = {
        "key": [0, 1, 2, 3, 4, 5],
        "date": [5, 4, 3, 2, 0, 1],
        "priority": [2, 1, 5, 0, 4],
        "deadline": [5, 4, 3, 2, 1]
    }

    add_tests = [
        {
            "name": "Add-1",
            "description": "Description One",
        },
        {
            "name": "Add-2",
            "description": "Description two",
        },
        {
            "name": "Add-3",
            "description": None,
        }
    ]

    @pytest.fixture()
    def mock_csv(self, tmp_path):
        store_path = tmp_path / "todo.csv"
        with store_path.open("w", newline='') as store:
            writer = csv.writer(store)
            writer.writerow(task_store.TaskStore.DEFAULT_CSV_HEADER)
            writer.writerows([task.to_list() for task in self.TASK_LIST])
        return store_path

    @pytest.mark.parametrize("sort, result_set",
                             [
                                 pytest.param(task_manager.SortType.KEY, TASK_SORT_RESULT_DICT["key"]),
                                 pytest.param(task_manager.SortType.DATE, TASK_SORT_RESULT_DICT["date"]),
                                 pytest.param(task_manager.SortType.PRIORITY, TASK_SORT_RESULT_DICT["priority"]),
                                 pytest.param(task_manager.SortType.DEADLINE, TASK_SORT_RESULT_DICT["deadline"])
                             ]
                             )
    class TestSorting:
        def test_get_tasks(self, mock_csv, sort, result_set):
            manager = task_manager.TaskManager(loadfile=mock_csv)
            sorted_list = manager.get_tasks(sort)

            for task, expected in zip(sorted_list, result_set):
                assert task == TestManager.TASK_LIST[expected]

        def test_get_tasks_reversed(self, mock_csv, sort, result_set):
            manager = task_manager.TaskManager(loadfile=mock_csv)
            sorted_list = manager.get_tasks(sort, True)
            for task, expected in zip(sorted_list, reversed(result_set)):
                assert task == self.TASK_LIST[expected]

    @pytest.mark.parametrize(
        "name, description",
        [
            pytest.param(
                add_tests[0]["name"],
                add_tests[0]["description"],
            ),
            pytest.param(
                add_tests[1]["name"],
                add_tests[1]["description"],
            ),
            pytest.param(
                add_tests[2]["name"],
                add_tests[2]["description"],
            ),
        ],
    )
    class TestAdd():

        def test_add(self, mock_csv, name, description):
            manager = task_manager.TaskManager(loadfile=mock_csv)
            task = manager.add_task(name, description)
            assert task.name == name
            assert task.description == description
            manager.load_from_file(str(mock_csv))
            read = manager.to_list()
            assert len(read) == len(TestManager.TASK_LIST) + 1

        def test_add_invalid_filename(self, mock_csv, name, description):
            manager = task_manager.TaskManager(loadfile="invalid.csv")

            with pytest.raises(FileNotFoundError):
                manager.add_task(name, description)
            manager.load_from_file(str(mock_csv))
            read = manager.to_list()
            assert len(read) == len(TestManager.TASK_LIST)

        @pytest.mark.parametrize(
            "iname",
            [
                pytest.param(None),
                pytest.param(" "),
                pytest.param(""),
            ],
        )
        def test_add_invalid_parameters(self, mock_csv, iname, name, description):
            manager = task_manager.TaskManager(loadfile="invalid.csv")

            with pytest.raises(exceptions.TaskNameError):
                manager.add_task(iname, description)
            manager.load_from_file(str(mock_csv))
            read = manager.to_list()
            assert len(read) == len(TestManager.TASK_LIST)

    @pytest.mark.parametrize(
        "name, description",
        [
            pytest.param(
                add_tests[0]["name"],
                add_tests[0]["description"],
            ),
            pytest.param(
                add_tests[1]["name"],
                add_tests[1]["description"],
            ),
            pytest.param(
                add_tests[2]["name"],
                add_tests[2]["description"],
            ),
        ],
    )
    class TestEdit:

        def test_edit(self, mock_csv, name, description):
            manager = task_manager.TaskManager(loadfile=mock_csv)
            manager.load_from_file(str(mock_csv))
            task = manager.edit_task(1, name, description)
            assert task.name == name
            if description is not None:
                assert task.description == description
            manager.load_from_file(str(mock_csv))
            task_from_file = manager.get_task(1)
            assert task.name == task_from_file.name

        @pytest.mark.parametrize(
            "iname",
            [
                pytest.param(" "),
                pytest.param(""),
            ],
        )
        def test_edit_invalid_parameters(self, mock_csv, iname, name, description):
            manager = task_manager.TaskManager(loadfile=str(mock_csv))
            manager.load_from_file(str(mock_csv))

            with pytest.raises(exceptions.TaskNameError):
                manager.edit_task(1, iname, description)
            manager.load_from_file(str(mock_csv))

    def test_clear(self, mock_csv):
        manager = task_manager.TaskManager(loadfile=str(mock_csv))
        manager.load_from_file(str(mock_csv))

        initial_len = len(manager.to_list())
        manager.clear_tasks()
        final_from_list = len(manager.to_list())

        manager.load_from_file(str(mock_csv))
        final_from_file = len(manager.to_list())

        assert initial_len != final_from_file == final_from_list
        assert final_from_file == 0 == final_from_list
        assert initial_len == len(self.TASK_LIST)

    @pytest.mark.parametrize(
        "task_id",
        list(range(1, 4)),
    )
    def test_delete(self, mock_csv, task_id):
        manager = task_manager.TaskManager(loadfile=str(mock_csv))
        manager.load_from_file(str(mock_csv))

        initial_len = len(manager.to_list())
        manager.delete_task(task_id)
        with pytest.raises(exceptions.TaskIDError):  # Check deleted from internal list
            manager.get_task(task_id)
        final_from_list = len(manager.to_list())

        manager.load_from_file(str(mock_csv))
        with pytest.raises(exceptions.TaskIDError):  # Check deleted from file
            manager.get_task(task_id)
        final_from_file = len(manager.to_list())

        assert final_from_file == len(self.TASK_LIST) - 1 == final_from_list
        assert initial_len == len(self.TASK_LIST)

    def test_delete_old(self, mock_csv):
        """
        Tests if past due tasks are deleted
        3 Completed, 3 Not
        5 Past due as of 20230127, 2 not
        """
        manager = task_manager.TaskManager(loadfile=str(mock_csv))
        manager.load_from_file(str(mock_csv))

        manager.delete_old_tasks()
        assert len(manager.to_list()) == 2

    def test_delete_completed(self, mock_csv):
        """
        Tests if completed tasks are deleted
        3 Completed, 3 Not
        5 Past due as of 20230127, 2 not
        """
        manager = task_manager.TaskManager(loadfile=str(mock_csv))
        manager.load_from_file(str(mock_csv))

        manager.delete_completed_tasks()
        assert len(manager.to_list()) == 3

    @pytest.mark.parametrize(
        "task_id",
        list(range(1, len(TASK_LIST) + 2)),
    )
    def test_complete(self, mock_csv, task_id):
        manager = task_manager.TaskManager(loadfile=str(mock_csv))
        manager.load_from_file(str(mock_csv))

        if task_id > len(self.TASK_LIST):
            with pytest.raises(exceptions.TaskIDError):
                manager.toggle_completion(task_id)
        else:
            initial = manager.get_task(task_id).completed
            manager.toggle_completion(task_id)
            final = manager.get_task(task_id).completed
            assert initial != final
