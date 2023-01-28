from datetime import datetime

from taskmn.priority import Priority
from taskmn.exceptions import DateException, TaskNameError


class Task:
    """
    A container class used to represent a Task

    Properties

    name : str
        The name of the task
    description : str
        A description of the task
    deadline : datetime
        The deadline for the task, can be None to represent no deadline
    priority : Priority
        The priority of the task
    completed : bool
        A bool representing task completion
    id : int
        A unique id representing a task
    created : datetime
        A timestamp showing the time and date the task was originally created

    Methods


    """
    last_id = 0

    def __init__(self, name, description=None, deadline=None, priority=None):
        """

        :param name: str The name of the task
        :param description: str (optional) a description of the task
        :param deadline: datetime (optional) a datetime representing the task's deadline
        :param priority: Priority (optional) the priority of the task
        """
        self.name = name
        self.description = description
        self.deadline = deadline
        self.priority = priority
        self.completed = False
        Task.last_id += 1
        self.__id = Task.last_id
        self.__created = datetime.now()

    @classmethod
    def load_from_data(cls, name, description, deadline, priority, task_id, created, completed):
        # noinspection GrazieInspection
        """
                Creates a task object by providing all data, take care to avoid duplicate ids
                :param str name: Name for the task
                :param str or None description: Short description of the task
                :param str or datetime or None deadline: deadline of the task
                :param Priority or int or None priority: priority of the task
                :param int task_id: id of the task
                :param str or datetime created: date created of the task
                :param bool completed: completion status of the task
                :return Task: Task object made with the specified parameters
                """
        task = cls(name, description, deadline, priority)
        task.__id = task_id
        if isinstance(created, datetime):
            task.__created = created
        else:
            task.__created = datetime.strptime(created, '%Y-%m-%d %H:%M:%S.%f')  # Handle any errors further up
        task.completed = completed
        Task.last_id -= 1  # As this should be an already existing task we do not need to update the last id
        return task

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, new_name):
        if new_name is None or str(new_name).isspace() or str(new_name) == '':
            raise TaskNameError(new_name)
        else:
            self.__name = str(new_name)

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, new_description):
        self.__description = new_description

    @property
    def deadline(self):
        return self.__deadline

    @deadline.setter
    def deadline(self, new_deadline):
        try:
            if new_deadline is None or new_deadline == 'None':
                self.__deadline = None
            elif isinstance(new_deadline, datetime):
                self.__deadline = new_deadline
            else:
                new_deadline_list = new_deadline.split(" ")  # Ignore time section is there is one
                self.__deadline = datetime.strptime(new_deadline_list[0], '%Y-%m-%d')
        except ValueError:  # Handle exception further up
            raise DateException(new_deadline)

    @property
    def created(self):
        return self.__created

    @property
    def priority(self):
        return self.__priority

    @priority.setter
    def priority(self, new_priority):
        if new_priority is None:
            self.__priority = Priority.NORMAL
        else:
            self.__priority = Priority(new_priority)

    @property
    def completed(self):
        return self.__completed

    @completed.setter
    def completed(self, bool_completed):
        if bool_completed is not None and isinstance(bool_completed, bool):
            self.__completed = bool_completed

    @property
    def id(self):
        return self.__id

    def __str__(self):
        return f"{self.id} {self.name} (Desc: {self.description} | Deadline: {self.deadline} | " \
               f"Priority: {self.priority} | Created: {self.created} | " \
               f"Completed: {'yes' if self.completed else 'no'})"

    def to_list(self, fancy=False):
        """
        Returns task object in a list representation
        :param fancy:
        :return:
        """
        if not fancy:
            return [str(self.__id), str(self.__name), str(self.__description), str(self.__deadline),
                    str(self.__priority.value), str(self.__created), str(int(self.__completed))]
        else:
            return [str(self.__id), str(self.__name), str(self.__description), str(self.__deadline).split(" ")[0],
                    str(self.__priority.name.capitalize()), str(self.__created).split(".")[0],
                    "Yes" if self.completed else "No"]

    def __eq__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return (self.name == other.name) and (self.deadline == other.deadline) and (self.id == other.id) and \
                (self.description == other.description) and (self.created == other.created) and \
                (self.priority == other.priority)
        return NotImplemented

    def __ne__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return not (self == other)
        return NotImplemented
