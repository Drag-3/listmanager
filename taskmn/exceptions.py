"""
This module contains all user defined exceptions used in Tasks Manager

    Classes

        DateException

        TaskNameError

        ConfigFileError

        ConfigDirectoryError

        StoreException

        StoreWriteException

        StoreCopyException

        TaskIDError

"""


class DateException(RuntimeError):
    """
    Error occurred while creating a date
    """
    def __init__(self, attempted):
        self.attempted = attempted
        self.message = f'Creating the date with "{attempted}" failed. Format is "YYYY-MM-DD"'
        super().__init__(self.message)

    def __str__(self):
        return self.message
    pass


class TaskNameError(RuntimeError):
    """
    An invalid task name was provided
    """
    def __init__(self, attempted):
        self.attempted = attempted
        self.message = f'Creating a task with "{attempted}" failed. Names must not be empty strings"'
        super().__init__(self.message)

    def __str__(self):
        return self.message
    pass


class ConfigFileError(OSError):
    """
    Error occurred reading or writing from the config file
    """
    def __init__(self, path):
        self.path = path
        self.message = f'Creating config file at "{path}"  has failed'

    def __str__(self):
        return self.message


class ConfigDirectoryError(OSError):
    """
    Error occurred creating the config dir
    """
    def __init__(self, path):
        self.path = path
        self.message = f'Creating config directory at "{path}"  has failed'

    def __str__(self):
        return self.message


class StoreException(OSError):
    """
    Error occurred with the task store
    """
    def __init__(self, path):
        self.path = path

    pass


class StoreWriteException(StoreException):
    """
    Error occurred writing to a task store
    """
    def __init__(self, path):
        super().__init__(path)
        self.message = f'Writing to the store at "{self.path}" has failed'

    def __str__(self):
        return self.message
    pass


class StoreReadException(StoreException):
    """
    Error occurred reading from a task store
    """
    def __init__(self, path):
        super().__init__(path)
        self.message = f'Reading the store at "{self.path}" has failed.'

    def __str__(self):
        return self.message
    pass


class StoreCopyException(StoreException):
    """
    Error occurred copying from a task store, could be creating writing, creating
    """
    def __init__(self, path, path2):
        super().__init__(path)
        self.path_2 = path2
        self.message = f'Copying "{self.path}" to "{path2}" has failed.'

    def __str__(self):
        return self.message
    pass


class TaskIDError(ValueError):
    """
    An invalid task id was inputted
    """
    def __init__(self, message):
        super().__init__(message)


class TagIDError(ValueError):
    """
    An invalid tag id was inputted
    """
    def __init__(self, message):
        super().__init__(message)

