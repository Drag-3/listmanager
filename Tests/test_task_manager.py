import csv

import pytest

from taskmn import task as TASK, task_manager, exceptions, task_store


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
