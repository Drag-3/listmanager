import configparser
import csv
import errno
import os
from pathlib import Path

from taskmn.exceptions import StoreWriteException, StoreReadException, StoreCopyException

"""
This Module will contain a class to manage the saving and loading of a TaskManager object to and from a .csv file

Classes
TaskStore 

Methods
get_storage_path(Path)
init_storage(Path)
"""


# noinspection GrazieInspection
def get_storage_path(config_file: Path) -> Path:
    """
    Reads the config file and gets the saved filestore path
    :param Path config_file: Path to the config file
    :return Path: Path as to which the task store will be located
    """
    config_parser = configparser.ConfigParser()
    config_parser.read(config_file)
    return Path(config_parser["General"]["Storage"])


def init_storage(store_path: Path):
    """
    Initializes a store by creating or overwriting the file and writing the header to the file.
    Same as TaskStore.save_to_csv([])

    :param store_path: The path to which the filestore will be created
    :return:
    """
    try:
        with open(store_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(TaskStore.DEFAULT_CSV_HEADER)
    except OSError:
        raise StoreWriteException(store_path)


class TaskStore:
    """
    Class which manages the storage and loading of Tasks into csv format

    --------------

    Static Properties

    DEFAULT_CSV_HEADER : list[string]
    DEFAULT_TASK_STORE_PATH : Path

    ---------------

    Attributes

    filename : str

    ---------------

    Methods

    save_to_csv(list[list[string]], list[string], sting)

    append_to_csv(list[string], string)

    edit_csv(int, list[string], string)

    load_from_csv(string)

    copy_csv(self, filename:  str = None, new_filename: str = None):

    """
    DEFAULT_CSV_HEADER = ['ID', 'Name', 'Description', 'Deadline', 'Priority', 'Created', 'Completed']
    DEFAULT_TASK_STORE_PATH = Path.home().stem + "_tasks.csv"

    def __init__(self, filename: str):
        self.store_filename = filename

    def save_to_csv(self, data, header=None, filename=None):
        """
        Saves data to a csv file. Will overwrite existing files

        :param list[list[string]] data: The data to save to the file, each the outer list is column, inner is row
        :param list[string] header: List containing a header for the csv file if a custom needed
        :param string filename: The file to save the results to. Will overwrite if already exists.
        :exception StoreWriteException: Creating or writing to the store failed
        """
        if filename is None:
            filename = self.store_filename
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                # Write header
                if header is None:
                    header = TaskStore.DEFAULT_CSV_HEADER
                writer.writerow(header)
                # Write data
                if len(data) > 0:
                    writer.writerows(data)
        except OSError:
            raise StoreWriteException(Path(filename))

    def append_to_csv(self, data, filename=None):
        """
        Appends to an existing csv file the entered data.  1 or more entries

        :param list[list[string]] data: The element to append to the csv file in list form
        :param string filename: The file to append to
        :exception FileNotFoundError: The file does not exist
        :exception StoreWriteException: Writing to the store failed
        """
        if filename is None:
            filename = self.store_filename
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        try:
            with open(filename, 'a', newline='') as file:
                writer = csv.writer(file)
                if len(data) > 0:
                    writer.writerows(data)
        except OSError:
            raise StoreWriteException(Path(filename))

    def edit_csv(self, task_id, data=None, filename:  str = None):
        """
        This will edit an existing csv file, replacing with data or deleting a row if data is None
        :param int task_id: The id of the task to edit
        :param list[list[string]] data: The data to replace the task with, if None the task is deleted
        :param string filename: The file to edit

        :exception FileNotFoundError: The file does not exist
        :exception StoreCopyException: Copying the store failed
        """
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        temp_filename = str(filename) + ".new"
        temp_file = open(temp_filename, "w", newline='')
        try:
            with open(filename, 'r', newline='') as file, temp_file:
                reader = csv.reader(file)
                writer = csv.writer(temp_file)

                for row in reader:  # Copy data to temp file, editing the specific task
                    if len(row) == 0:  # skip padding rows
                        continue
                    if row[0] == str(task_id):
                        if data is None:  # Delete the file by skipping it in the copy
                            continue
                        else:
                            row = data[0]  # replace the original data with teh entered data
                    writer.writerow(row)

            os.remove(filename)
            os.rename(temp_filename, filename)
        except OSError:
            raise StoreCopyException(Path(filename), Path(temp_filename))

    def load_from_csv(self, filename: str = None, ids_to_load: list[int] = None):
        """
        Loads the data from a csv file and returns it as a tuple

        :param list[str] ids_to_load: A list of task id's to load from the Store
        :param string filename: The file to load
        :return (int, list[list[string]]: A tuple containing the maximum id, and the file's data
        :exception FileNotFoundError: The specified file does not exist
        :exception StoreReadException: Reading the data from the Store failed
        """
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        task_list = []
        max_id = 0
        try:
            with open(filename, 'rU', newline='') as file:
                reader = csv.reader(file)
                print(reader)
                header = next(reader)

                print(header)
                if TaskStore.DEFAULT_CSV_HEADER != header:  # If the header does not match, the file is invalid
                    raise StoreReadException(Path(filename))
                if not ids_to_load:  # Load all tasks to the list
                    for row in reader:
                        if len(row) == 0:
                            continue
                        task_list.append(row)
                        max_id = max(max_id, int(row[0]))
                else:  # Load specified tasks to the list. If empty throw away the loaded tasks and just return id
                    # task_list = [line for line in reader]
                    for row in reader:
                        if len(row) == 0:
                            continue
                        if int(row[0]) in ids_to_load:
                            task_list.append(row)
                        max_id = max(max_id, int(row[0]))
        except OSError as e:
            print(e)
            print(e.errno)
            print(e.strerror)
            print(e.filename)
            print(e.args)
            raise StoreReadException(Path(filename))
        except Exception as e:
            print(e)
            print(e.args)
            print(e.__str__())
            raise e

        return max_id, task_list

    def copy_csv(self, filename:  str = None, new_filename: str = None):
        """
        This will copy an existing csv file, to a specified file. This will not remove the data in the old file
        :param str new_filename: The file to copy to
        :param string filename: The file to copy from

        :exception FileNotFoundError: The file does not exist
        :exception FileExistsError: Attempt to copy to the same file
        :exception StoreCopyException: Copying the store failed
        """
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if new_filename is None or new_filename.isspace() or new_filename == '':
            raise StoreWriteException(Path(str(new_filename)))

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        if filename == os.path.abspath(new_filename):
            raise FileExistsError("Can not copy a path to itself")
        try:
            with open(filename, 'r', newline='') as file, open(new_filename, 'w', newline='') as new_file:
                reader = csv.reader(file)
                writer = csv.writer(new_file)

                for row in reader:  # Copy data to new file
                    if len(row) == 0:  # skip padding rows
                        continue
                    writer.writerow(row)
            self.store_filename = new_filename
        except OSError:
            raise StoreCopyException(Path(filename), Path(str(new_filename)))
