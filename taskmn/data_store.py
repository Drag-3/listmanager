# TODO Remember to add setup to the config area and here
"""
Class Draft
__init__()
set up filename



FROM MANAGER
to add a filter use                   addFilter("filtername")
to add a task to a filter             addTaskFilter(filter ID, taskID)
to remove a task from a filter        removeTaskFilter(filter ID, taskID)
to remove a filter use                removeFilter(filterID)
to get all tags use                getFilters() -> filter name filter id tuple
to clear all tags                  query all the tags, then run remove filter for each

FROM CLI
to add a filter use                   add filter "filtername"
to add a task to a filter use         edit task_id -f "filtername" | or ID
to remove a task from a filter use    edit task_id -rf "filtername" | or ID
to remove a filter use                remove filter "filtername"   | or ID
to list all filter use                ls tags


"""
import configparser
import errno
import itertools
import os
from contextlib import contextmanager
from pathlib import Path
import shutil
from sqlite3 import IntegrityError

from taskmn.exceptions import StoreWriteException, StoreReadException, StoreCopyException
from taskmn import task


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


def get_storage_path(config_file: Path) -> Path:
    """
    Reads the config file and gets the saved filestore path
    :param Path config_file: Path to the config file
    :return Path: Path as to which the task store will be located
    """
    config_parser = configparser.ConfigParser()
    config_parser.read(config_file)
    return Path(config_parser["General"]["Storage"])


def get_stored_filters(config_file: Path) -> list:
    config_parser = configparser.ConfigParser()
    config_parser.read(config_file)
    filters = []
    for section in config_parser.sections():
        filter_dict = dict(config_parser[section])
        filters.append(filter_dict)
    return filters


def init_storage(store_path: Path):
    try:
        conn = sql.connect(store_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS tag(tag_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "                                  tag_name TEXT NOT NULL)")
        cur.execute("CREATE TABLE IF NOT EXISTS task(task_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "                                task_name TEXT NOT NULL,"
                    "                                task_description TEXT,"
                    "                                task_deadline DATE,"
                    "                                task_priority integer,"
                    "                                task_created timestamp NOT NULL,"
                    "                                task_completed BOOL)"
                    )
        cur.execute("CREATE TABLE IF NOT EXISTS tag_task(tag_id INTEGER NOT NULL, task_id INTEGER NOT NULL,"
                    "                                       FOREIGN KEY (tag_id) REFERENCES tag(tag_id),"
                    "                                       FOREIGN KEY (task_id) REFERENCES task(task_id))")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS tag_task_unq ON tag_task(tag_id, task_id)")
        conn.execute("CREATE UNIQUE INDEX uq_tag_name ON tag(tag_name);")
        conn.close()

    except OSError as e:
        raise e


class DataStore:
    """
        DataStore class provides methods for managing a database of tasks and tags.

        Attributes:
            DEFAULT_DATA_STORE_PATH (str): The default file path for the database.

        Methods:
            - Connection Methods
            get_conn: Get a connection object for the database
            get_conn_and_cursor: Get a connection and cursor for the database
            - Tag Methods
            add_tag: Add a tag to the database
            remove_tag; Remove a tag from the database
            edit_tag: Edit a tag contained in the database
            load_tags: Load all tags in the databse, an optional requirement is a list of tasks the tags must correspond
            - Task Methods
            add_task: Add a task to the database
            remove_task: Remove a task from the database
            load_tasks: Load tasks from the database based on specified parameters.
            load_tags: Load tags from the database.
            load_tag_tasks: Load tag-task relationships from the database.
            add_task: Add a new task to the database.
            add_tag: Add a new tag to the database.
            update_task: Update an existing task in the database.
            update_tag: Update an existing tag in the database.
            delete_task: Delete a task from the database.
            delete_tag: Delete a tag from the database.
            get_conn: Get a connection to the database.
            get_conn_and_cursor: Get a connection and cursor to the database.
            copy_database: Copy an existing database to a new file.
            clear_tasks: Clear tasks from the database.
            clear_tags: Clear tags from the database.
        """
    DEFAULT_DATA_STORE_PATH = Path.home().stem + "_taskmn.db"

    def __init__(self, filename: str | Path = None):
        if not isinstance(filename, Path) and (filename is None or filename.isspace() or filename == ''):
            self.store_filename = DataStore.DEFAULT_DATA_STORE_PATH
        else:
            self.store_filename = str(filename)

    @contextmanager
    def get_conn(self, path: str):
        conn = None
        try:
            conn = sql.connect(path)
            # Set the max to the highest id, to help prevent big gaps developing
            conn.execute("UPDATE sqlite_sequence SET seq = (SELECT MAX(task_id) FROM task) WHERE name = 'task';")
            conn.execute("UPDATE sqlite_sequence SET seq = (SELECT MAX(tag_id) FROM tag) WHERE name = 'tag';")
            conn.commit()

            yield conn
        except OSError as e:
            print("Error getting conn")
            raise e
        finally:
            if conn:
                conn.close()

    # Instead of passing the string pass a list representation like the task_store

    def add_tag(self, name: str, filename: str = None):
        try:
            with self.get_conn_and_cursor(filename) as (conn, curr):
                query = "INSERT INTO tag (tag_name) VALUES (?)"
                curr.execute(query, [name])
                conn.commit()
                return curr.lastrowid, name  # Filter Tuple
        except IntegrityError:
            raise ValueError(f"Tag {name} already exists")

    def remove_tag(self, tag_id: str | int, filename: str = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            if isinstance(tag_id, str):
                curr.execute("SELECT tag_id FROM tag WHERE tag_name = ?", (tag_id,))
                tag_id = curr.fetchone()[0]

            curr.execute("DELETE FROM tag where tag_id = ?", (tag_id,))
            conn.commit()
            curr.execute("DELETE FROM tag_task WHERE tag_id = ?", (tag_id,))
            conn.commit()

            return tag_id

    def append_tags_task(self, task_id: int, tag_id_list: list[int], filename=None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            if tag_id_list is None or len(tag_id_list) == 0:
                raise AttributeError("Invalid task")
            else:
                query = f"""
                INSERT INTO tag_task (tag_id, task_id) 
                SELECT f.tag_id, t.task_id 
                FROM tag f, task t 
                WHERE (t.task_id = ?) AND tag_id in ({','.join(['?'] * len(tag_id_list))})
                AND NOT EXISTS (
            SELECT 1 FROM tag_task WHERE tag_id = f.tag_id AND task_id = t.task_id
            )"""
                values = [task_id] + tag_id_list
                curr.execute(query, values)

            conn.commit()

    def remove_tag_task(self, task_id: int, tag_id_list: list[int], filename=None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            query = f"""
            DELETE FROM tag_task 
            WHERE (task_id = ?)
            AND tag_id in ({','.join(['?'] * len(tag_id_list))})
            """
            values = [task_id] + tag_id_list
            curr.execute(query, values)
            conn.commit()

    def edit_tag(self, tag_id: int, new_name: str, filename: str = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            curr.execute(f"UPDATE tag SET tag_name = ? WHERE tag_id = ?", (new_name, tag_id))
            conn.commit()

    def load_tags(self, filename: str = None, ids_to_load: list[int] = None, tasks: list[int] = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):

            # Add Code to Select based on filter only one filter is allowed
            query = "SELECT t.* FROM tag t\n"
            if ids_to_load or tasks:
                query += "WHERE "
                if ids_to_load:
                    query += f"t.tag_id IN ({','.join(['?'] * len(ids_to_load))})"
                    if tasks:
                        query += " AND "
                if tasks:
                    query += f"t.tag_id IN (SELECT tag_id FROM tag_task" \
                             f" WHERE task_id IN ({','.join(['?'] * len(tasks))}))"

                values = list(itertools.chain.from_iterable((ids_to_load or [], tasks or [])))
                curr.execute(query, values)
            else:
                curr.execute(query)

            results = curr.fetchall()
            return results

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

        with self.get_conn_and_cursor(filename) as (conn, curr):
            query = """INSERT INTO task 
            (task_name, task_description, task_deadline, task_priority, task_created, task_completed) VALUES 
                            (?, ?, ?, ?, ?, ?)"""

            values = (data[1], data[2], data[3], data[4], data[5], data[6])
            curr.execute(query, values)
            conn.commit()
            return curr.lastrowid

    def edit_task(self, task_id, data=None, filename: str = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            query = f"""UPDATE task SET 
                                task_name = COALESCE(?, task_name),
                                task_description = COALESCE(?, task_description),
                                task_deadline = COALESCE(?, task_deadline),
                                task_priority = COALESCE(?,task_priority),
                                task_created = COALESCE(?, task_created),
                                task_completed = COALESCE(?, task_completed)
                        WHERE task_id = ?;"""

            values = (data[1], data[2], data[3], data[4], data[5], data[6], task_id)
            curr.execute(query, values)
            conn.commit()

    def remove_tasks(self, filename: str = None, ids_to_remove: list[int] = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):

            if ids_to_remove is None or len(ids_to_remove) == 0:
                self.clear_tasks(filename)
            else:
                query = f"DELETE FROM task WHERE task_id in ({','.join(['?'] * len(ids_to_remove))})"
                curr.execute(query, ids_to_remove)
                conn.commit()
                query = f"DELETE FROM tag_task WHERE task_id in ({','.join(['?'] * len(ids_to_remove))})"
                curr.execute(query, ids_to_remove)
                conn.commit()

    """
    SELECT t.*
    FROM tasks t
    JOIN task_filter tf ON t.id = tf.task_id
    WHERE tf.tag_id IN (1, 2, 3)
    
    """

    def load_tag_tasks(self, filename: str = None, tag_id: int = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            query = """SELECT * FROM tag_task WHERE tag_id = ?"""
            curr.execute(query, (tag_id,))
            out = curr.fetchall()
            tag_tasks = {tag_id: [row[1] for row in out if row[0] == tag_id] for tag_id in set(row[0] for row in out)}

            return tag_tasks

    def load_task_tags(self, filename: str = None, task_id: int = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            query = """SELECT * FROM tag_task WHERE task_id = ?"""
            curr.execute(query, (task_id,))
            out = curr.fetchall()
            task_tags = {task_id: [row[0] for row in out if row[1] == task_id] for task_id in set(row[1] for row in out)}

            return task_tags

    def tag_has_tasks(self, filename: str = None, tags=None):
        if tags is None:
            tags = []
        with self.get_conn_and_cursor(filename) as (conn, curr):
            if tags:
                tag_id_placeholders = ', '.join(['?' for _ in tags])

            query = f"""
                SELECT tag.tag_id, CASE WHEN COUNT(task.task_id) > 0 THEN 1 ELSE 0 END AS has_tasks
                FROM tag
                LEFT JOIN tag_task ON tag.tag_id = tag_task.tag_id
                LEFT JOIN task ON tag_task.task_id = task.task_id
                {'WHERE tag.tag_id IN (' + tag_id_placeholders + ')' if tags else ''}
                GROUP BY tag_task.tag_id
            """

            curr.execute(query, tags)

            results = curr.fetchall()

            tag_task_status = {}
            for tag_id, has_tasks in results:
                tag_task_status[tag_id] = bool(has_tasks)

            return tag_task_status

    def task_has_tags(self, filename: str = None, tasks=None):
        if tasks is None:
            tasks = []
        with self.get_conn_and_cursor(filename) as (conn, curr):
            if tasks:
                task_id_placeholders = ', '.join(['?' for _ in tasks])

            query = f"""
                    SELECT task.task_id, CASE WHEN COUNT(tag.tag_id) > 0 THEN 1 ELSE 0 END AS has_tags
                    FROM task
                    LEFT JOIN tag_task ON task.task_id = tag_task.task_id
                    LEFT JOIN tag ON tag_task.tag_id = tag.tag_id
                    {'WHERE task.task_id IN (' + task_id_placeholders + ')' if tasks else ''}
                    GROUP BY tag_task.task_id
                """

            curr.execute(query, tasks)

            results = curr.fetchall()

            tag_task_status = {}
            for tag_id, has_tasks in results:
                tag_task_status[tag_id] = bool(has_tasks)

            return tag_task_status

    def load_tasks(self, filename: str = None, ids_to_load: list[int] = None, tags: list[int] = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):

            # Add Code to Select based on filter only one filter is allowed
            query = "SELECT t.* FROM task t\n"
            if ids_to_load or tags:
                query += "WHERE "
                if ids_to_load:
                    query += f"t.task_id IN ({','.join(['?'] * len(ids_to_load))})"
                    if tags:
                        query += " AND "
                if tags:
                    query += f"t.task_id IN (SELECT task_id FROM tag_task" \
                             f" WHERE tag_id IN ({','.join(['?'] * len(tags))}))"

                values = list(itertools.chain.from_iterable((ids_to_load or [], tags or [])))
                curr.execute(query, values)
            else:
                curr.execute(query)

            results = curr.fetchall()
            return results

    @contextmanager
    def get_conn_and_cursor(self, filename):
        if filename is None or filename.isspace() or filename == '':
            filename = self.store_filename
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        with self.get_conn(filename) as conn:
            curr = conn.cursor()
            yield conn, curr

    def copy_database(self, new_filename: str, filename: str = DEFAULT_DATA_STORE_PATH):
        """
        This will copy an existing database to a new file. This will not remove the data in the old file
        :param str new_filename: The file to copy to
        :param string filename: The file to copy from

        :exception FileNotFoundError: The file does not exist
        :exception FileExistsError: Attempt to copy to the same file
        :exception StoreCopyException: Copying the store failed
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        if os.path.abspath(filename) == os.path.abspath(new_filename):
            raise FileExistsError("Can not copy a path to itself")

        try:
            shutil.copy(filename, new_filename)
        except OSError:
            raise StoreCopyException(Path(filename), Path(new_filename))

    def clear_tasks(self, *, filename: str = None, condition: str = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):

            if condition is None:
                curr.execute("DELETE FROM task")
                conn.commit()
                curr.execute("DELETE FROM tag_task")
                conn.commit()
            else:
                curr.execute(f"DELETE FROM task WHERE ({condition})")
                conn.commit()
                curr.execute(f"DELETE FROM tag_task WHERE task_id NOT IN (SELECT task_id FROM task)")
                conn.commit()

    def clear_tags(self, filename: str = None, condition: str = None):
        with self.get_conn_and_cursor(filename) as (conn, curr):
            if condition is None:
                curr.execute("DELETE FROM tag")
                conn.commit()
                curr.execute("DELETE FROM tag_task")
                conn.commit()
            else:
                curr.execute(f"DELETE FROM tag WHERE ({condition})")
                conn.commit()
                curr.execute(f"DELETE FROM tag_task WHERE tag_id NOT IN (SELECT tag_id FROM tag)")
                conn.commit()


class FilterManager:
    def __init__(self, tasks=None, loadfile=DataStore.DEFAULT_DATA_STORE_PATH):
        self.loadfile = str(loadfile)
        if tasks is not None:
            self.__tasks = tasks
        else:
            self.__tasks = []
            self.__store = DataStore(loadfile)


if __name__ == "__main__":
    # Testing
    X = DataStore()

    # Z = X.load_tasks(None, [2], [2])
    # print(Z)

    # Swap value if completed
    task = X.load_tasks()
    print(task)
    tag = X.load_tags()
    print(tag)
    tags = X.tag_has_tasks(None, [2])
    taskss = X.task_has_tags(None, [2])
    y = X.load_tag_tasks(None, 1)
    print(taskss)
    print(tags)
    pass

    # Complete as normal, then create a new Task with a returned id and add that to the internal list
"""
[id name data] - list representation
"""
