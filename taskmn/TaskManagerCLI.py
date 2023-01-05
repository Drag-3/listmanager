from typing import Optional
from pathlib import Path

import click.exceptions
import typer
from tabulate import tabulate
from rich import print
from rich.panel import Panel

from taskmn import __app_name__, __version__, config, exceptions
from taskmn import TaskStore
from taskmn.TaskManager import TaskManager, SortType


def _version_callback(value: bool):
    """
    Print's application Name and version before Exiting
    :param value:
    :return:
    """
    if value:
        print(f"{__app_name__} [green]v[/green]{__version__}")
        raise typer.Exit()


VALID_SORTS = ["key", "deadline", "created", "priority"]


def _complete_sort_type(incomplete: str):
    completion = []
    for sort in VALID_SORTS:
        if sort.startswith(incomplete):
            completion.append(sort)
    return completion


def _exception_box(message: str):
    """
    Puts the message in a fancy box
    :param message:
    :return:
    """
    print(Panel.fit(message, title="Exception"))


def _info_box(message: str):
    """
    Puts the message in a fancy box
    :param message:
    :return:
    """
    print(Panel.fit(message, title="Info"))


app = typer.Typer()


@app.callback()
def run(version: Optional[bool] = typer.Option(
    None,
    "--version",
    "-v",
    help="Show the application's version and exit.",
    callback=_version_callback,
    is_eager=True
)
) -> None:
    return


@app.command()
def init(store_path: str = typer.Option(
    str(TaskStore.TaskStore.DEFAULT_TASK_STORE_PATH),
    "--store-path",
    "-s",
    prompt="Task Manager Store location?"
),
):
    """
    Creates the config file and the storage csv file whose name is provided
    """
    try:
        config.init_app(Path(store_path))
    except OSError as e:
        _exception_box(f'[bold red]Creating config failed with {e}.[/bold red]')
        raise typer.Exit(1)
    else:
        _info_box(f"[green]Config file successfully created.[/green]")
    try:
        TaskStore.init_storage(Path(store_path))
    except OSError as e:
        _exception_box(f'[bold red]Creating Storage failed with {e}.[/bold red]')
        raise typer.Exit(1)
    else:
        _info_box(f"[green]The Store is at {store_path}.[green]")


def get_manager():
    """
    Creates a TaskManager object attached to the storage defined by init()
    """
    if config.CONFIG_FILE_PATH.exists():
        store_path = TaskStore.get_storage_path(config.CONFIG_FILE_PATH)
    else:
        _exception_box(f"[bold red]Configuration file not found. Run 'taskmn init' and try again[/bold red]")
        raise typer.Exit(1)
    if store_path.exists():
        return TaskManager(loadfile=store_path)
    else:
        _exception_box(f"[bold red]Store file not found. Run 'taskmn init' and try again[/bold red]")
        raise typer.Exit(1)


@app.command()
def add(
        name: str = typer.Argument(..., help="Name of the task"),
        description: str = typer.Option(None, "--description", "-desc", help="Description for the task"),
        deadline: str = typer.Option(None, "--deadline", "-dl", help="Deadline for the task"),
        priority: int = typer.Option(1, "--priority", "-p", min=0, max=2, help="Priority for the task")
):
    """
    Adds a task to the list
    """
    manager = get_manager()
    try:
        manager.load_from_file()  # Get the list of Tasks from memory, in order to properly set the id of the new Task
        task = manager.add_task(name, description, deadline, priority)
    except Exception as e:
        _exception_box(f"[bold redAdding task failed with {e}[/bold red]")
    else:
        _info_box(f"[green]Adding Task #{task.id} - {task.name} Complete![/green]")


@app.command(name="list")
def list_all(
        sort: str = typer.Option("key", "--sort", "-s",
                                 help="How to sort the list [key/deadline/created/priority]",
                                 autocompletion=_complete_sort_type),
        reverse: Optional[bool] = typer.Option(False, "--reverse", "-r", help="Reverses the outputted list")
):
    """
    Lists all the stored tasks in a pretty table using tabulate
    """
    manager = get_manager()
    manager.load_from_file()
    match sort.strip().lower():
        case "key":
            task_list = manager.get_tasks(SortType.KEY, reverse)
        case "created":
            task_list = manager.get_tasks(SortType.DATE, reverse)
        case "deadline":
            task_list = manager.get_tasks(SortType.DEADLINE, reverse)
        case "priority":
            task_list = manager.get_tasks(SortType.PRIORITY, reverse)
        case _:
            _exception_box(f"[bold red]{sort} is not a valid option for -s [/bold red]"
                           f"[bold green]\[key/deadline/created/priority][/bold green]")
            raise typer.Exit(1)

    if len(task_list) == 0:
        _info_box("You have no tasks yet [yellow]:)[/yellow]")
    else:
        table = tabulate([task.to_list(True) for task in task_list], TaskStore.TaskStore.DEFAULT_CSV_HEADER,
                         tablefmt="grid", maxcolwidths=[None, 25])
        print(table)
    typer.Exit()


@app.command()
def complete(
        task_id: int = typer.Argument(None, min=1, help="The id of the task to change the completion status")
):
    """
    Flips the completion status of the indicated task
    """
    manager = get_manager()
    manager.load_from_file()
    try:
        task = manager.change_completion(task_id)
    except ValueError:
        _exception_box(f"[bold red]Task #{task_id} does not exist[/bold red]")
        raise typer.Exit(1)
    _info_box(f"Task #{task_id} - {task.name} [bold green]marked as complete[/bold green]") if task.completed else \
        _info_box(f"Task #{task_id} - {task.name} [bold green]marked as incomplete[/bold green]")
    raise typer.Exit()


@app.command()
def delete(
        task_id: int = typer.Argument(..., min=1, help="The id of the task to delete"),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation dialog")
):
    """
    Deletes the indicated task
    """
    manager = get_manager()
    manager.load_from_file()
    try:
        task = manager.get_task(task_id)
        if not force:
            confirmation = typer.confirm(f"Are you sure you want to delete #{task_id} - {task.name}?")
            if confirmation:
                manager.delete_task(task_id)
            else:
                _info_box("[bold red]Delete Aborted[/bold red]")
                raise typer.Exit()
        else:
            manager.delete_task(task_id)
    except ValueError:
        _exception_box(f"[bold red]Task #{task_id} does not exist[/bold red]")
        raise typer.Exit(1)
    _info_box(f"Task #{task_id} [bold red]deleted[/bold red]")
    raise typer.Exit()


@app.command()
def edit(
        task_id: int = typer.Argument(..., min=1, help="The id of the task to edit"),
        name: str = typer.Option(None, "--name", "-n", help="Name of the task"),
        description: str = typer.Option(None, "--description", "-desc", help="Description for the task"),
        deadline: str = typer.Option(None, "--deadline", "-dl", help="Deadline for the task"),
        priority: int = typer.Option(None, "--priority", "-p", min=0, max=2, help="Priority for the task"),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation dialog")
):
    """
    Edits the indicated task
    """
    if name is None and description is None and deadline is None and priority is None:
        _exception_box("[bold red]At least one option is required for editing[/bold red]")
        raise typer.Exit(1)
    manager = get_manager()
    manager.load_from_file()
    try:
        task = manager.get_task(task_id)
        if not force:
            confirmation = typer.confirm(f"Are you sure you want to edit #{task_id} - {task.name}?")
            if confirmation:
                manager.edit_task(task_id, name, description, deadline, priority)
            else:
                _info_box("[bold red]Edit Aborted[/bold red]")
                raise typer.Exit()
        else:
            manager.edit_task(task_id, name, description, deadline, priority)
    except ValueError:
        _exception_box(f"[bold red]Task #{task_id} does not exist[/bold red]")
        raise typer.Exit(1)
    except click.exceptions.Exit as e:  # Already printed details for typer.Exit()
        raise e
    except Exception as e:
        _exception_box(f"[bold red]Edit failed with {e}[/bold red]")
        raise typer.Exit(1)
    _info_box(f"[bold green]Edited Task #{task_id} - {task.name}[/bold green]")
    raise typer.Exit()


@app.command()
def clear(force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation dialog")
          ):
    """
    Clears all tasks
    """
    manager = get_manager()
    manager.load_from_file()

    if not force:
        confirmation = typer.confirm(f"Are you sure you want to clear all tasks?")
        if confirmation:
            manager.clear_tasks()
        else:
            _info_box("[bold red]Delete Aborted[/bold red]")
            raise typer.Exit()
    else:
        manager.clear_tasks()
    _info_box(f"All tasks[bold red]deleted[/bold red]")
    raise typer.Exit()


@app.command(name="config")
def modify_config(store_path: str = typer.Option(None,
                                                 "--modify-path",
                                                 "-m",
                                                 help=f"New Task Manager Store location"
                                                      f" ie [{TaskStore.TaskStore.DEFAULT_TASK_STORE_PATH}]"
                                                 ),
                  want_path: Optional[bool] = typer.Option(False,
                                                           "--store-path", "-s",
                                                           help="Print the current Task store name")
                  ):
    """
    Provides some configuration options
    """
    if want_path:
        _info_box(f"The store location is '{TaskStore.get_storage_path(config.CONFIG_FILE_PATH)}'")
        raise typer.Exit()
    if store_path is None:
        _exception_box("[bold red]An option is required (-s, -m)[/bold red]")
        raise typer.Exit(1)
    elif store_path.isspace() or store_path == "":
        _exception_box(f'[bold red]Must enter a store path "{store_path}" is invalid[/bold red]')
        raise typer.Exit(1)

    try:
        old_store = str(TaskStore.get_storage_path(config.CONFIG_FILE_PATH))
        store = TaskStore.TaskStore(old_store)
        store.copy_csv(old_store, store_path)

    except FileNotFoundError:
        _exception_box(f'[bold red]Store file not found, try running "taskmn init".[/bold red]')
        raise typer.Exit(1)
    except exceptions.StoreCopyException as e:
        _exception_box(f"[bold red]Copying the task store has failed. {e.path} --> {e.path_2}[/bold red]")
        raise typer.Exit(1)
    try:  # Do config last to minimize chance of loosing data if somthing happens to the stores
        config.modify_config_file(store_path)
    except exceptions.ConfigFileError:
        _exception_box("[bold red]Modifying the configuration file has failed.[/bold red]")
    else:
        _info_box(f"[green]The Store is now at {store_path}.[green]")
