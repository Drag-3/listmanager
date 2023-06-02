import datetime
import operator
import sqlite3
from enum import Enum

from taskmn.exceptions import TaskIDError, TagIDError
from taskmn.task import Task
from taskmn.tag import Tag
from taskmn.data_store import DataStore

"""
Module contains a task which controls and manages Task objects

Classes

SortType(Enum)

TaskManager
"""


class SortType(Enum):
    """
    A class used to represent a value to sort by
    """
    KEY = 0
    DATE = 1
    DEADLINE = 2
    PRIORITY = 3


# Depreciated
# def create_taskmanager_metadata():
#   return [Task.last_id, str(datetime.datetime.now())]


class TaskManager:
    """
    A class used to manage a list of Task objects

    Properties:
        _tasks : List<Task> A list object which stores all the tasks
        _store : TaskStore Object that manages storage and loading

    Methods:

        show_all_tasks() -> None
        get_task(int) -> Task
        get_tasks(SortType, bool) -> list
        delete_old_tasks() -> None
        delete_completed_tasks() -> None
        add_task(str, str, datetime || str, Priority || int) -> None
        edit_task(int, str, str,  datetime || str, Priority || int) -> None
        mark_complete(int) -> None
        to_list() -> None
        save_to_file(string) -> None
        load_from_file(str || Path) -> None
    """

    def __init__(self, tasks=None, *, loadfile=DataStore.DEFAULT_DATA_STORE_PATH, filters: list[dict] = None):
        self.loadfile = str(loadfile)
        self._filters = filters
        if tasks is not None:
            self._tasks = tasks
        else:
            self._tasks = []
            self._store = DataStore(loadfile)

    def show_all_tasks(self):
        """
        Prints all the tasks to the console using str()
        """
        print(self)

    def __str__(self):
        string = ''
        for task in self.load_tasks_from_file():
            string += (str(task) + '\n')
        return string

    def get_task(self, task_id):
        """
        Given an id returns the associated Task object

        :param int task_id: (int) The id of the task to get
        :return: (Task) The task the user entered the id for
        :exception TaskIDError: raises TaskIDError if task's id does not exist in _tasks
        """
        task = self.load_tasks_from_file(id_list=[task_id])
        if task:
            return task[0]
        raise TaskIDError(f"Task (id = {task_id}) does not exist")

    """
    I plan to eliminate the internal list of this class and only use it as a wrapper for the Datastore object
    Each function will however pull required lists into memory to otherwise display or act upon them
    """

    def get_tasks(self, *, sort: SortType = SortType.KEY, reverse: bool = False, tags: list[int] = None) -> list:
        """
        Returns a list containing all stored Tasks. Optional parameters can be used to sort the produced list

        :param SortType or int sort: (optional) Provide a SortType to change the sorting method. Default is by ID
        :param bool reverse: (optional) reverses the sort method:
        :return: Returns all stored tasks in list form
        """
        tasks = self.load_tasks_from_file(tag_list=tags)
        if SortType(sort) == SortType.KEY:
            return sorted(tasks, key=operator.attrgetter('id'), reverse=reverse)
        elif SortType(sort) == SortType.DATE:
            return sorted(tasks, key=operator.attrgetter('created'), reverse=reverse)
        elif SortType(sort) == SortType.DEADLINE:  # If deadline is None compare the smallest value we can get
            return sorted(tasks,
                          key=lambda task: task.deadline or datetime.datetime(datetime.MINYEAR, 1, 1),
                          reverse=reverse)
        elif SortType(sort) == SortType.PRIORITY:  # Priority wll sort high to low on default because it seems better
            return sorted(tasks, key=operator.attrgetter('priority'), reverse=not reverse)
        else:
            return tasks

    def add_task(self, name, description=None, deadline=None, priority=None):
        """
        Appends a new task to _tasks

        :param str name: The name of the task
        :param str or None description: (optional) a short description of the task
        :param datetime or str or None deadline: (optional) The deadline for the task
        :param Priority or int or None priority: (optional) The priority of the task
        """
        task = Task(name, description, deadline, priority).to_list()
        max_int = self._store.add_task(task)
        task[0] = max_int
        return Task.load_from_data(int(task[0]), task[1], task[2], task[3], int(task[4]), task[5],
                                   bool(int(task[6])))  # Completed)

    def edit_task(self, task_id, name=None, description=None, deadline=None, priority=None):
        """
            Edits a task given the task's id exists in _tasks

            :param int task_id: The id of the task to edit
            :param str or None name: The name of the task
            :param str or None description: (optional) a short description of the task
            :param datetime or str or None deadline: (optional) The deadline for the task
            :param Priority or int or None priority: (optional) The priority of the task
            :exception TaskIDError: Throws TaskIDError if id does not exist in _tasks
                """
        task = self.get_task(task_id)
        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if deadline is not None:
            task.deadline = deadline
        if priority is not None:
            task.priority = priority

        self._store.edit_task(task_id, task.to_list())
        return task

    def delete_task(self, task_id):
        """
        Deletes task from _tasks
        :param int task_id:
        :exception TaskIDError: Throws TaskIDError if id does not exist in _tasks
        """
        self._store.remove_tasks(ids_to_remove=[task_id])

    def delete_old_tasks(self):
        """
        Deletes all tasks which the deadline has passed the system time
        :return:
        """
        self._store.clear_tasks(condition=f"task_completed = "
                                          f"task_deadline IS NOT NULL AND task_deadline < DATETIME('now')")
        # self._tasks[:] = [task for task in self._tasks if
        #                   not (task.deadline is not None and task.deadline < datetime.datetime.now())]
        # self._store.save_to_csv(self.to_list())

    def delete_completed_tasks(self):
        """
        Deletes all tasks marked as complete
        :return:
        """
        self._store.clear_tasks(condition="task_completed = TRUE")
        # self._tasks[:] = [task for task in self._tasks if not task.completed]
        # self._store.save_to_csv(self.to_list())

    def clear_tasks(self):
        """
        Clears all tasks from task storage+
        :return:
        """
        self._store.clear_tasks()
        Task.last_id = 0

    def toggle_completion(self, task_id):
        """
        This toggles the completion property of the selected task

        :param int task_id: The id of the task to toggle
        :exception TaskIDError: Throws TaskIDError if id does not exist in _tasks
        """
        task = self.get_task(task_id)
        task.completed = not task.completed
        self._store.edit_task(task_id, task.to_list())
        return task

    def to_list(self):
        """
        Returns this object in list[list[string]] form
        :return list[list[string]: _tasks with all tasks converted to list[string]
        """
        built_list = []
        for task in self.load_tasks_from_file():
            built_list.append(task.to_list())
        return built_list

    def save_to_file(self, filename=None):
        """
        Saves data to a specific csv file
        :param string filename: Path to save to
        """
        if filename is None:
            filename = self.loadfile
        self._store.save_to_csv(self.to_list(), filename=filename)

    def load_tasks_from_file(self, *, filename: str = None, id_list: list[int] = None, tag_list: list[int] = None):
        """
        Loads a list of stacks from the designated storage
        :param tag_list: A list consisting of tag ids that are put over
        :param id_list: A list consisting of the task ids that should be loaded if they exist. if None all are loaded
        :param filename: File to load from
        """
        if filename is None:
            filename = self.loadfile
        task_list = self._store.load_tasks(filename, id_list, tag_list)
        self._tasks.clear()  # As all additions are immediately stored, not clearing will lead to duplicates
        tasks = []
        for task in task_list:
            tasks.append(
                Task.load_from_data(int(task[0]), task[1], task[2], task[3], int(task[4]), task[5], bool(int(task[6]))))
        return tasks

    def load_tags_from_file(self, *, filename: str = None, tasks_to_filter: list[int] = None,
                            tags_to_load: list[int] = None):
        if filename is None:
            filename = self.loadfile
        tag_list = self._store.load_tags(filename, tags_to_load, tasks_to_filter)
        tags = []
        for tag in tag_list:
            tags.append(Tag.load_from_data(tag[0], tag[1]))
        return tags

    def add_tag(self, tag_name: str):
        try:
            tag_id, _ = self._store.add_tag(tag_name)
            return Tag.load_from_data(tag_id, tag_name)
        except ValueError:
            raise ValueError(f"Tag '{tag_name}' already exists.")

    def remove_tag(self, tag_identifier: str | int):
        try:
            tag_id = self._store.remove_tag(tag_identifier)
            return tag_id
        except ValueError:
            raise TagIDError(f"Tag '{tag_identifier}' does not exist.")

    def get_tags(self, filter_task: list[int] = None):
        tags = self.load_tags_from_file(tasks_to_filter=filter_task)
        # Add sorting if required later
        return tags

    def get_tag(self, tag_id):
        tag = self.load_tags_from_file(tags_to_load=tag_id)
        if tag:
            return tag[0]
        raise TagIDError(f"Tag (id = {tag_id}) does not exist")

    def task_has_tags(self, task_list=None):
        return self._store.task_has_tags(self.loadfile, task_list)

    def tag_has_tasks(self, tag_list=None):
        return self._store.tag_has_tasks(self.loadfile, tag_list)

    def get_task_tags(self, task_id: int):
        return self._store.load_task_tags(self.loadfile, task_id)

    def get_tag_tasks(self, tag_id: int):
        return self._store.load_tag_tasks(self.loadfile, tag_id)
    def clear_tags(self):
        self._store.clear_tags()

    def clear_unlinked_tags(self):
        self._store.clear_tags(condition=
                               "SELECT COUNT(*) FROM tag"
                               " LEFT JOIN tag_task ON tag.tag_id = tag_task.tag_id"
                               " WHERE tag_task.tag_id IS NULL")

    def add_tags_to_task(self, task_id: int, tags: list[int]):
        try:
            self._store.append_tags_task(task_id, tags)
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_tags_from_task(self, task_id: int, tags: list[int]):
        try:
            self._store.remove_tag_task(task_id, tags)
            return True
        except sqlite3.IntegrityError:
            return False


if __name__ == "__main__":
    manager = TaskManager()
    print(manager.to_list())

    manager.delete_old_tasks()

    print(manager.to_list())
