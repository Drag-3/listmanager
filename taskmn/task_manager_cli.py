import datetime
from pathlib import Path
from typing import Optional

import click.exceptions
import rich.table
import typer
from rich import print
from rich.panel import Panel

from taskmn import __app_name__, __version__, config, exceptions, task_store
from taskmn.docs import app as docs_app
from taskmn.task_manager import TaskManager, SortType


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


def _complete_sort_type(ctx, param, incomplete: str):
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
app.add_typer(docs_app, name="docs", help="Generate documentation")


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


@app.command(rich_help_panel="Files")
def init(store_path: str = typer.Option(
    str(task_store.TaskStore.DEFAULT_TASK_STORE_PATH),
    "--store-path",
    "-s",
    prompt="Task Manager Store location?"
),
        exists: bool = typer.Option(False, "--exist", "-e", help="The file specified by -s already exists")
):
    """
    Creates the config file and the storage csv file whose name is provided
    """
    try:
        config.init_app(Path(store_path), exists)
    except OSError as e:
        _exception_box(f'[bold red]Creating config failed with {e}.[/bold red]')
        raise typer.Exit(1)
    else:
        _info_box(f"[green]Config file successfully created.[/green]")
    try:
        if not exists:
            task_store.init_storage(Path(store_path))
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
        store_path = task_store.get_storage_path(config.CONFIG_FILE_PATH)
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
        deadline: str = typer.Option(None, "--deadline", "-dl", help="Deadline for the task. (YYYY-MM-DD)"),
        priority: int = typer.Option(1, "--priority", "-p", min=0, max=2, help="Priority for the task")
):
    """
    Adds a task to the list
    """
    manager = get_manager()
    try:
        manager.load_from_file(id_list=[])  # Make sure the last id is correctly set
        task = manager.add_task(name, description, deadline, priority)
    except Exception as e:
        _exception_box(f"[bold red]Adding task failed with {e}[/bold red]")
    else:
        _info_box(f"[green]Adding Task #{task.id} - {task.name} Complete![/green]")


@app.command(rich_help_panel="List")
def ls(
        sort: str = typer.Option("key", "--sort", "-s",
                                 help="How to sort the list [key/deadline/created/priority]",
                                 shell_complete=_complete_sort_type),
        reverse: Optional[bool] = typer.Option(False, "--reverse", "-r", help="Reverses the outputted list")
):
    """
    Alias for list
    """
    list_all(sort, reverse)


@app.command(name="list", rich_help_panel="List")
def list_all(
        sort: str = typer.Option("key", "--sort", "-s",
                                 help="How to sort the list [key/deadline/created/priority]",
                                 shell_complete=_complete_sort_type),
        reverse: Optional[bool] = typer.Option(False, "--reverse", "-r", help="Reverses the outputted list")
):
    """
    Lists all the stored tasks in a pretty table.
    """
    manager = get_manager()
    manager.load_from_file()  # Load up all tasks to output
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
        table = rich.table.Table(title="Tasks", show_lines=True, show_edge=True)

        for element in task_store.TaskStore.DEFAULT_CSV_HEADER:
            table.add_column(element, min_width=len(element) if (len(element) < 25) else 25, max_width=50)
        for task in task_list:
            task2 = task.to_list(True)

            # Style the outputted table
            if task.completed:
                task2[6] = f"[green]{task2[6]}[/green] :heavy_check_mark:"
            if task.deadline is not None and task.deadline < datetime.datetime.now():
                task2[3] = f"[bold red]{task2[3]}[/bold red]"
            else:
                task2[3] = f"[green]{task2[3]}[/green]"
            match task.priority.value:
                case 1:
                    task2[4] = f"[yellow]{task2[4]}[/yellow]"
                case 2:
                    task2[4] = f"[green]{task2[4]}[/green]"
            table.add_row(*task2)

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
    manager.load_from_file(id_list=[task_id])
    try:
        task = manager.toggle_completion(task_id)
    except ValueError:
        _exception_box(f"[bold red]Task #{task_id} does not exist[/bold red]")
        raise typer.Exit(1)
    _info_box(f"Task #{task_id} - {task.name} [bold green]marked as complete[/bold green]") if task.completed else \
        _info_box(f"Task #{task_id} - {task.name} [bold green]marked as incomplete[/bold green]")
    raise typer.Exit()


@app.command(rich_help_panel="Delete")
def rm(
        task_id: int = typer.Argument(..., min=0, help="The id of the task to delete."),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation dialog"),
):
    """
    Alias for delete
    """
    delete(task_id, force)


@app.command(rich_help_panel="Delete")
def delete(
        task_id: int = typer.Argument(..., min=0, help="The id of the task to delete."),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation dialog"),
):
    """
    Deletes the indicated task
    """
    manager = get_manager()
    manager.load_from_file(id_list=[task_id])
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
        deadline: str = typer.Option(None, "--deadline", "-dl", help="Deadline for the task (YYYY-MM-DD)"),
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
    manager.load_from_file(id_list=[task_id])
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


def _par_del_options(manager, del_completed, del_old, force):
    if not (del_completed or del_old):
        return
    if del_completed and del_old:
        _exception_box("[bold red] Flags -c and -p are exclusive")
        raise typer.Exit(1)
    if del_completed:
        _del_completed(manager, force)
    else:
        _del_old(manager, force)
    _info_box(f"[bold red]deleted[/bold red]")
    raise typer.Exit()


def _del_old(manager, force):
    if not force:
        confirmation = typer.confirm(f"Are you sure you want to delete all tasks which the deadline has passed?")
        if confirmation:
            manager.delete_old_tasks()
        else:
            _info_box("[bold red]Delete Aborted[/bold red]")
            raise typer.Exit()
    else:
        manager.delete_old_tasks()


def _del_completed(manager, force):
    if not force:
        confirmation = typer.confirm(f"Are you sure you want to delete all completed tasks?")
        if confirmation:
            manager.delete_old_tasks()
        else:
            _info_box("[bold red]Delete Aborted[/bold red]")
            raise typer.Exit()
    else:
        manager.delete_completed_tasks()


@app.command(rich_help_panel="Delete", )
def clear(force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation dialog"),
          del_completed: bool = typer.Option(False, "--completed", "-c", help="Delete all completed", is_eager=True),
          del_old: bool = typer.Option(False, "--past-due", "-p", help="Delete all past due", is_eager=True),
          ):
    """
    Clears multiple tasks depending on options. None specified clears all tasks.
    """
    manager = get_manager()
    manager.load_from_file()  # Load all tasks in order to clear/ filter effectively

    if not force:
        _par_del_options(manager, del_completed, del_old, force)
        confirmation = typer.confirm(f"Are you sure you want to clear all tasks?")
        if confirmation:
            manager.clear_tasks()
        else:
            _info_box("[bold red]Delete Aborted[/bold red]")
            raise typer.Exit()
    else:
        _par_del_options(manager, del_completed, del_old, force)
        manager.clear_tasks()
    _info_box(f"All tasks[bold red]deleted[/bold red]")
    raise typer.Exit()


@app.command(name="config", rich_help_panel="Files")
def modify_config(store_path: str = typer.Option(None,
                                                 "--modify-path",
                                                 "-m",
                                                 help=f"New Task Manager Store location"
                                                      f" ie [{task_store.TaskStore.DEFAULT_TASK_STORE_PATH}]"
                                                 ),
                  want_path: Optional[bool] = typer.Option(False,
                                                           "--store-path", "-s",
                                                           help="Print the current Task store name")
                  ):
    """
    Provides some configuration options
    """
    if want_path:
        _info_box(f"The store location is '{task_store.get_storage_path(config.CONFIG_FILE_PATH)}'")
        raise typer.Exit()
    if store_path is None:
        _exception_box("[bold red]An option is required (-s, -m)[/bold red]")
        raise typer.Exit(1)
    elif store_path.isspace() or store_path == "":
        _exception_box(f'[bold red]Must enter a store path "{store_path}" is invalid[/bold red]')
        raise typer.Exit(1)

    try:
        old_store = str(task_store.get_storage_path(config.CONFIG_FILE_PATH))
        store = task_store.TaskStore(old_store)
        store.copy_csv(old_store, store_path)

    except FileNotFoundError:
        _exception_box(f'[bold red]Store file not found, try running "taskmn init".[/bold red]')
        raise typer.Exit(1)
    except exceptions.StoreCopyException as e:
        _exception_box(f"[bold red]Copying the task store has failed. {e.path} --> {e.path_2}[/bold red]")
        raise typer.Exit(1)
    try:  # Do config last to minimize chance of loosing data if something happens to the stores
        config.modify_config_file(store_path)
    except exceptions.ConfigFileError:
        _exception_box("[bold red]Modifying the configuration file has failed.[/bold red]")
    else:
        _info_box(f"[green]The Store is now at {store_path}.[green]")
