import datetime
import operator
from enum import Enum
from taskmn.task import Task
from taskmn.task_store import TaskStore
from taskmn.exceptions import TaskIDError

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
        __tasks : List<Task> A list object which stores all the tasks
        __store : TaskStore Object that manages storage and loading

    Methods:

        show_all_tasks() -> None
        get_task(int) -> Task
        get_tasks(SortType, bool) -> list
        add_task(str, str, datetime || str, Priority || int) -> None
        edit_task(int, str, str,  datetime || str, Priority || int) -> None
        mark_complete(int) -> None
        to_list() -> None
        save_to_file(string) -> None
        load_from_file(str || Path) -> None
    """

    def __init__(self, tasks=None, loadfile=TaskStore.DEFAULT_TASK_STORE_PATH):
        self.loadfile = str(loadfile)
        if tasks is not None:
            self.__tasks = tasks
        else:
            self.__tasks = []
            self.__store = TaskStore(loadfile)

    def show_all_tasks(self):
        """
        Prints all the tasks to the console using str()
        """
        print(self)

    def __str__(self):
        string = ''
        for task in self.__tasks:
            string += (str(task) + '\n')
        return string

    def get_task(self, task_id):
        """
        Given an id returns the associated Task object

        :param int task_id: (int) The id of the task to get
        :return: (Task) The task the user entered the id for
        :exception TaskIDError: raises TaskIDError if task's id does not exist in __tasks
        """
        for task in self.__tasks:
            if task.id == task_id:
                return task
        raise TaskIDError(f"Task (id = {task_id}) does not exist")

    def get_tasks(self, sort: SortType = SortType.KEY, reverse: bool = False) -> list:
        """
        Returns a list containing all stored Tasks. Optional parameters can be used to sort the produced list

        :param SortType or int sort: (optional) Provide a SortType to change the sorting method. Default is by ID
        :param bool reverse: (optional) reverses the sort method:
        :return: Returns all stored tasks in list form
        """
        if SortType(sort) == SortType.KEY:
            return sorted(self.__tasks, key=operator.attrgetter('id'), reverse=reverse)
        elif SortType(sort) == SortType.DATE:
            return sorted(self.__tasks, key=operator.attrgetter('created'), reverse=reverse)
        elif SortType(sort) == SortType.DEADLINE:  # If deadline is None compare the smallest value we can get
            return sorted(self.__tasks,
                          key=lambda task: task.deadline or datetime.datetime(datetime.MINYEAR, 1, 1),
                          reverse=reverse)
        elif SortType(sort) == SortType.PRIORITY:  # Priority wll sort high to low on default because it seems better
            return sorted(self.__tasks, key=operator.attrgetter('priority'), reverse=not reverse)
        else:
            return self.__tasks

    def add_task(self, name, description=None, deadline=None, priority=None):
        """
        Appends a new task to __tasks

        :param str name: The name of the task
        :param str or None description: (optional) a short description of the task
        :param datetime or str or None deadline: (optional) The deadline for the task
        :param Priority or int or None priority: (optional) The priority of the task
        """
        task = Task(name, description, deadline, priority)
        self.__tasks.append(task)
        self.__store.append_to_csv([task.to_list()])
        return task

    def edit_task(self, task_id, name=None, description=None, deadline=None, priority=None):
        """
            Edits a task given the task's id exists in __tasks

            :param int task_id: The id of the task to edit
            :param str or None name: The name of the task
            :param str or None description: (optional) a short description of the task
            :param datetime or str or None deadline: (optional) The deadline for the task
            :param Priority or int or None priority: (optional) The priority of the task
            :exception TaskIDError: Throws TaskIDError if id does not exist in __tasks
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
        self.__store.edit_csv(task_id, [task.to_list()])
        return task

    def delete_task(self, task_id):
        """
        Deletes task from __tasks
        :param int task_id:
        :exception TaskIDError: Throws TaskIDError if id does not exist in __tasks
        """
        task = self.get_task(task_id)
        self.__tasks.remove(task)
        self.__store.edit_csv(task_id)

    def delete_old_tasks(self):
        """
        Deletes all tasks which the deadline has passed the system time
        :return:
        """
        self.__tasks[:] = [task for task in self.__tasks if
                           not (task.deadline is not None and task.deadline < datetime.datetime.now())]
        self.__store.save_to_csv(self.to_list())

    def delete_completed_tasks(self):
        """
        Deletes all tasks marked as complete
        :return:
        """
        self.__tasks[:] = [task for task in self.__tasks if not task.completed]
        self.__store.save_to_csv(self.to_list())

    def clear_tasks(self):
        """
        Clears all tasks from task storage
        :return:
        """
        self.__store.save_to_csv([])
        self.__tasks.clear()
        Task.last_id = 0

    def toggle_completion(self, task_id):
        """
        This toggles the completion property of the selected task

        :param int task_id: The id of the task to toggle
        :exception TaskIDError: Throws TaskIDError if id does not exist in __tasks
        """
        task = self.get_task(task_id)
        task.completed = not task.completed
        self.__store.edit_csv(task_id, [task.to_list()])
        return task

    def to_list(self):
        """
        Returns this object in list[list[string]] form
        :return list[list[string]: __tasks with all tasks converted to list[string]
        """
        built_list = []
        for task in self.__tasks:
            built_list.append(task.to_list())
        return built_list

    def save_to_file(self, filename=None):
        """
        Saves data to a specific csv file
        :param string filename: Path to save to
        """
        if filename is None:
            filename = self.loadfile
        self.__store.save_to_csv(self.to_list(), filename=filename)

    def load_from_file(self, filename=None):
        """
        Loads a list of stacks from the designated storage
        :param filename: File to load from
        """
        if filename is None:
            filename = self.loadfile
        load_tuple = self.__store.load_from_csv(filename)
        Task.last_id = load_tuple[0]
        self.__tasks.clear()  # As all additions are immediately stored, not clearing will lead to duplicates
        for task in load_tuple[1]:
            self.__tasks.append(Task.load_from_data(task[1],  # Name
                                                    task[2],  # Description
                                                    task[3],  # Deadline
                                                    int(task[4]),  # Priority
                                                    int(task[0]),  # ID
                                                    task[5],  # Created datetime
                                                    bool(int(task[6]))  # Completed
                                                    ))
