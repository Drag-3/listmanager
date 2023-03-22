# TODO Remember to add setup to the config area and here
"""
Class Draft
__init__()
set up filename

load(filename, type(Name or list def Name) name(None if of type name) -> list[int] | list[str]
load data from the json file

save(filename, data)

Where do I want to save the loaded info?
Perhaps just load and parse the info here and return the list we want
To Add a record, pass the Name and task. ie Add("Best FIlter", task_id) -> we will create a new record or update the record based on it

To remove enter the filter name and the task id.

If you can, figure out how to send a different message to the user based on the state of the filter.
FROM MANAGER
to add a filter use                   addFilter("filtername")
to add a task to a filter             addTaskFilter(filter ID, taskID)
to remove a task from a filter        removeTaskFilter(filter ID, taskID)
to remove a filter use                removeFilter(filterID)
to get all filters use                getFilters() -> filter name filter id tuple
to clear all filters                  query all the filters, then run remove filter for each

FROM CLI
to add a filter use                   add filter "filtername"
to add a task to a filter use         edit task_id -f "filtername" | or ID
to remove a task from a filter use    edit task_id -rf "filtername" | or ID
to remove a filter use                remove filter "filtername"   | or ID
to list all filter use                ls filters


"""

import json
from pathlib import Path

import configparser
import csv
import errno
import os
from pathlib import Path
import shutil

from taskmn.exceptions import StoreWriteException, StoreReadException, StoreCopyException
from taskmn import task



def _json_encoder(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj


def _to_sets(obj):
    if isinstance(obj, list):
        return set(obj)
    elif isinstance(obj, dict):
        return {key: set(value) for key, value in obj.items()}
    return obj


class Filter:
    max_id = 0

    def __init__(self, name: str, task_list: set[int]):
        self.name = name
        self.task_list = task_list
        self.id = Filter.max_id + 1
        Filter.max_id += 1

    def to_tuple(self):
        return self.name, self.task_list, self.id


import sqlite3 as sql


def init_storage(store_path: Path):
    try:
        conn = sql.connect(store_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS filter(filter_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "                                  filter_name TEXT NOT NULL)")
        cur.execute("CREATE TABLE IF NOT EXISTS task(task_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "                                task_name TEXT NOT NULL,"
                    "                                task_description TEXT,"
                    "                                task_deadline DATE,"
                    "                                task_priority integer,"
                    "                                task_created timestamp NOT NULL,"
                    "                                task_completed BOOL)"
                    )
        cur.execute("CREATE TABLE IF NOT EXISTS filter_task(filter_id INTEGER NOT NULL, task_id INTEGER NOT NULL,"
                    "                                       FOREIGN KEY (filter_id) REFERENCES filter(id),"
                    "                                       FOREIGN KEY (task_id) REFERENCES task(id))")
        conn.execute("CREATE UNIQUE INDEX filter_task_unq ON filter_task(filter_id, task_id)")
        conn.close()

    except OSError as e:
        raise e


class DataStore:
    DEFAULT_FILTER_STORE_PATH = Path.home().stem + "_filters.db"

    def __init__(self, filename: str = None):
        if filename is None or filename.isspace() or filename == '':
            self.store_filename = DataStore.DEFAULT_FILTER_STORE_PATH
        else:
            self.store_filename = filename

    def getConn(self, path: str):
        try:
            conn = sql.connect(path)
            return conn
            conn.close()
        except OSError as e:
            print("Error getting conn")
            raise e

    # Instead of passing the string pass a list representation like the task_store

    def add_filter(self, name: str, filename: str = None):
        if filename is None or filename == "" or filename.isspace():
            filename = DataStore.DEFAULT_FILTER_STORE_PATH

        conn = self.getConn(filename)
        cur = conn.cursor()
        cur.execute(f"""
        INSERT INTO filter (filter_name) VALUES
        ('{name}')
        """)
        conn.commit()

    def remove_filter(self, name: str = None, filter_id: int = None, filename: str = None):
        if filename is None or filename == "" or filename.isspace():
            filename = DataStore.DEFAULT_FILTER_STORE_PATH

        conn = self.getConn(filename)
        cur = conn.cursor()
        if filter_id is None:
            cur.execute(f"SELECT filter_id FROM filter WHERE filter_name = '{name}'")
            filter_id = cur.fetchall()

        cur.execute(f"DELETE FROM filter where filter_id = {filter_id}")
        conn.commit()
        cur.execute(f"DELETE FROM filter_task WHERE filter_id = {filter_id}")
        conn.commit()

    def append_task_filter(self, task_id_list: list, filter_name: str = None, filter_id: int = None, filename=None):
        if filename is None or filename == "" or filename.isspace():
            filename = DataStore.DEFAULT_FILTER_STORE_PATH

        conn = self.getConn(filename)
        curr = conn.cursor()
        if task_id_list is None or len(task_id_list) == 0:
            raise AttributeError("Invalid task")
        else:
            query = f"""
            INSERT INTO filter_task (filter_id, task_id) 
            SELECT f.filter_id, t.task_id 
            FROM filter f, task t 
            WHERE (f.filter_name = '{filter_name}' OR f.filter_id = {filter_id}) AND task_id in ({','.join(['?'] * len(task_id_list))})"""
            curr.execute(query, task_id_list)

        conn.commit()

    def remove_task_filter(self, task_id_list: list, filter_name: str = None, filter_id: int = None, filename=None):
        if filename is None or filename == "" or filename.isspace():
            filename = DataStore.DEFAULT_FILTER_STORE_PATH

        conn = self.getConn(filename)
        cur = conn.cursor()
        cur.execute(f"""
        DELETE FROM filter_task 
        WHERE (filter_id = {filter_id} OR filter_name = {filter_name}) 
        AND task_id in ({','.join(['?'] * len(task_id_list))})
        """, task_id_list)
        conn.commit()

    def edit_filter(self, filter_name, new_name: str = None, new_data: set = None, filename: str = None):
        pass

    def load_json(self, filename=None):
        pass

    def add_task(self, data, filename=None):
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
            conn = self.getConn(filename)
            curr = conn.cursor()
            curr.execute(f"""INSERT INTO task (name, description, deadline, Priority, Created, completed) VALUES 
                            ('{data[1]}', '{data[2]}','{data[3]}',{data[4]},'{data[5]}',{data[6]})""")

            conn.commit()
            return curr.lastrowid
        except OSError:
            raise StoreWriteException(Path(filename))

    def edit_task(self, task_id, data=None, filename: str = None):
        """
        This will edit an existing csv file, replacing with data or deleting a row if data is None
        :param int task_id: The id of the task to edit
        :param list[list[string]] data: The data to replace the task with, if None the task is deleted
        :param string filename: The file to edit

        :exception FileNotFoundError: The file does not exist
        :exception StoreCopyException: Copying the store failed
        """

        if filename is None:
            filename = self.store_filename
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        try:
            conn = self.getConn(filename)
            curr = conn.cursor()
            curr.execute(f"""UPDATE task SET name = COALESCE('{data[1]}', name),
                                            description = COALESCE('{data[2]}', description),
                                            deadline = COALESCE('{data[3]}', deadline),
                                            Priority = COALESCE('{data[4]}', Priority),
                                            Created = COALESCE('{data[5]}', Created),
                                            completed = COALESCE('{data[6]}', completed)
                            WHERE task_id = {task_id};""")

            conn.commit()
        except OSError:
            raise StoreWriteException(Path(filename))

    def remove_tasks(self, filename: str = None, ids_to_remove: list[int] = None):
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        conn = self.getConn(filename)
        curr = conn.cursor()

        if ids_to_remove is None or len(ids_to_remove) == 0:
            self.clear_tasks(filename)
        else:
            query = f"DELETE FROM task WHERE task_id in ({','.join(['?'] * len(ids_to_remove))})"
            curr.execute(query, ids_to_remove)
            conn.commit()
            query = f"SELECT * FROM filter_task WHERE task_id in ({','.join(['?'] * len(ids_to_remove))})"
            curr.execute(query, ids_to_remove)
            conn.commit()

    """
    SELECT t.*
    FROM tasks t
    JOIN task_filter tf ON t.id = tf.task_id
    WHERE tf.filter_id IN (1, 2, 3)
    
    """
    def load_tasks(self, filename: str = None, ids_to_load: list[int] = None, filters: list[int] = None):
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        conn = self.getConn(filename)
        curr = conn.cursor()

        # Add Code to Select based on filter only one filter is allowed
        query = "SELECT t.* FROM task t\n"
        if filter is None or len(filters) == 0:
            if ids_to_load is None or len(ids_to_load) == 0:
                curr.execute(query)
            else:
                query += f"WHERE t.task_id in ({','.join(['?'] * len(ids_to_load))})\n"
                curr.execute(query, ids_to_load)
        else:
            query += f"JOIN filter_task ft ON t.task_id = ft.task_id\n" \
                     f"WHERE ft.filter_id IN ({','.join(str(e) for e in filters)})\n"

            if ids_to_load is None or len(ids_to_load) == 0:
                curr.execute(query)
            else:
                query += f"AND t.task_id in ({','.join(['?'] * len(ids_to_load))})\n"
                curr.execute(query, ids_to_load)
        conn.commit()
        results = curr.fetchall()

        return results

    def copy_database(self, filename: str = None, new_filename: str = None):
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
            shutil.copy(filename, new_filename)
        except OSError:
            raise StoreCopyException(Path(filename), Path(str(new_filename)))

    def clear_tasks(self, filename: str):
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        conn = self.getConn(filename)
        curr = conn.cursor()

        curr.execute("DELETE FROM task")
        conn.commit()
        curr.execute("DELETE FROM filter_task")
        conn.commit()

    def clear_filters(self, filename: str):
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename

        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        conn = self.getConn(filename)
        curr = conn.cursor()

        curr.execute("DELETE FROM filter")
        conn.commit()
        curr.execute("DELETE FROM filter_task")
        conn.commit()


class FilterManager:
    def __init__(self, tasks=None, loadfile=DataStore.DEFAULT_FILTER_STORE_PATH):
        self.loadfile = str(loadfile)
        if tasks is not None:
            self.__tasks = tasks
        else:
            self.__tasks = []
            self.__store = DataStore(loadfile)


if __name__ == "__main__":
    # Testing
    X = DataStore()

    # X.add_filter("Type 1")
    # X.add_filter("Type 2")
    #tTask = task.Task('Test')
    #tl = tTask.to_list()
    # X.append_to_csv(tl, filename=None)
    # tTask.description = "Edited Desc"
    # X.edit_csv(1, tTask.to_list())
    # X.remove_task_filter('Type 2', 1)
    #X.remove_task_filter([2], filter_id=1)
    # X.append_task_filter("Type 3", 12)
    # X.edit_filter("Type 1", new_name="Type 1 Edited", new_data={1, 3, 5, 7, 9})
    # D = X.load_json()
    Z = X.load_tasks(None, [2], [2])
    print(Z)
    pass

    # Complete as normal, then create a new Task with a returned id and add that to the internal list
"""
[id name data] - list representation
"""
