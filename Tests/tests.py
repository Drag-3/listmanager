import csv

import pytest
from typer.testing import CliRunner

import taskmn
from taskmn import __app_name__, __version__, TaskManagerCLI, Task, TaskManager, exceptions

runner = CliRunner()


def test_version():
    """
    Test passes if the result of -v and --version print the correct info
    :return:
    """
    result = runner.invoke(TaskManagerCLI.app, ["--version"])
    assert result.exit_code == 0
    assert f"{__app_name__} v{__version__}\n" in result.stdout
    result = runner.invoke(TaskManagerCLI.app, ["-v"])
    assert result.exit_code == 0
    assert f"{__app_name__} v{__version__}\n" in result.stdout


@pytest.fixture
def mock_csv(tmp_path):
    Task.Task.last_id = 0
    task = Task.Task("Name", "Description", "2002-03-03", 2)
    store_path = tmp_path / "todo.csv"
    with store_path.open("w") as store:
        writer = csv.writer(store)
        writer.writerow(["Fake", "Header"])
        writer.writerow(task.to_list())
    return store_path


add_test_1 = {
    "name": "Add-1",
    "description": "Description One",
    "task": Task.Task("Add-1", "Description One", priority=0)
}
add_test_2 = {
    "name": "Add-2",
    "description": "Description two",
    "task": Task.Task("Add-1", "Description One", deadline="2023-02-01")
}
add_test_3 = {
    "name": "Add-3",
    "description": None,
    "task": Task.Task("Add-1", None, deadline="2023-02-01")
}


@pytest.mark.parametrize(
    "name, description",
    [
        pytest.param(
            add_test_1["name"],
            add_test_1["description"],
        ),
        pytest.param(
            add_test_2["name"],
            add_test_2["description"],
        ),
        pytest.param(
            add_test_3["name"],
            add_test_3["description"],
        ),
    ],
)
class TestAdd:

    def test_add(self, mock_csv, name, description):
        manager = taskmn.TaskManager.TaskManager(loadfile=mock_csv)
        task = manager.add_task(name, description)
        assert task.name == name
        assert task.description == description
        manager.load_from_file(str(mock_csv))
        read = manager.to_list()
        assert len(read) == 2

    def test_add_invalid_filename(self, mock_csv, name, description):

        manager = taskmn.TaskManager.TaskManager(loadfile="invalid.csv")

        with pytest.raises(FileNotFoundError):
            manager.add_task(name, description)
        manager.load_from_file(str(mock_csv))
        read = manager.to_list()
        assert len(read) == 1

    @pytest.mark.parametrize(
        "iname",
        [
            pytest.param(None),
            pytest.param(" "),
            pytest.param(""),
        ],
    )
    def test_add_invalid_parameters(self, mock_csv, iname, name, description):

        manager = taskmn.TaskManager.TaskManager(loadfile="invalid.csv")

        with pytest.raises(exceptions.TaskNameError):
            manager.add_task(iname, description)
        manager.load_from_file(str(mock_csv))
        read = manager.to_list()
        assert len(read) == 1


@pytest.mark.parametrize(
    "name, description",
    [
        pytest.param(
            add_test_1["name"],
            add_test_1["description"],
        ),
        pytest.param(
            add_test_2["name"],
            add_test_2["description"],
        ),
        pytest.param(
            add_test_3["name"],
            add_test_3["description"],
        ),
    ],
)
class TestEdit:

    def test_edit(self, mock_csv, name, description):
        manager = taskmn.TaskManager.TaskManager(loadfile=mock_csv)
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

        manager = taskmn.TaskManager.TaskManager(loadfile=str(mock_csv))
        manager.load_from_file(str(mock_csv))

        with pytest.raises(exceptions.TaskNameError):
            manager.edit_task(1, iname, description)
        manager.load_from_file(str(mock_csv))


def test_clear(mock_csv):
    manager = taskmn.TaskManager.TaskManager(loadfile=str(mock_csv))
    manager.load_from_file(str(mock_csv))

    manager.add_task("One")
    manager.add_task("Two")
    initial_len = len(manager.to_list())
    manager.clear_tasks()
    final_from_list = len(manager.to_list())

    manager.load_from_file(str(mock_csv))
    final_from_file = len(manager.to_list())

    assert initial_len != final_from_file == final_from_list
    assert final_from_file == 0 == final_from_list
    assert initial_len == 3


@pytest.mark.parametrize(
    "task_id",
    list(range(1, 4)),
)
def test_delete(mock_csv, task_id):
    manager = taskmn.TaskManager.TaskManager(loadfile=str(mock_csv))
    manager.load_from_file(str(mock_csv))

    manager.add_task("One")
    manager.add_task("Two")
    initial_len = len(manager.to_list())
    manager.delete_task(task_id)
    with pytest.raises(exceptions.TaskIDError):  # Check deleted from internal list
        manager.get_task(task_id)
    final_from_list = len(manager.to_list())

    manager.load_from_file(str(mock_csv))
    with pytest.raises(exceptions.TaskIDError):  # Check deleted from file
        manager.get_task(task_id)
    final_from_file = len(manager.to_list())

    assert final_from_file == 2 == final_from_list
    assert initial_len == 3

