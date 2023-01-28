# `taskmn`

**Usage**:

```console
$ taskmn [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-v, --version`: Show the application's version and exit.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `add`: Adds a task to the list
* `clear`: Clears multiple tasks depending on options.
* `complete`: Flips the completion status of the...
* `config`: Provides some configuration options
* `delete`: Deletes the indicated task
* `docs`: Generate documentation
* `edit`: Edits the indicated task
* `init`: Creates the config file and the storage...
* `list`: Lists all the stored tasks in a pretty table.
* `ls`: Alias for list
* `rm`: Alias for delete

## `taskmn add`

Adds a task to the list

**Usage**:

```console
$ taskmn add [OPTIONS] NAME
```

**Arguments**:

* `NAME`: Name of the task  [required]

**Options**:

* `-desc, --description TEXT`: Description for the task
* `-dl, --deadline TEXT`: Deadline for the task. (YYYY-MM-DD)
* `-p, --priority INTEGER RANGE`: Priority for the task  [default: 1; 0<=x<=2]
* `--help`: Show this message and exit.

## `taskmn clear`

Clears multiple tasks depending on options. None specified clears all tasks.

**Usage**:

```console
$ taskmn clear [OPTIONS]
```

**Options**:

* `-f, --force`: Skip confirmation dialog
* `-c, --completed`: Delete all completed
* `-p, --past-due`: Delete all past due
* `--help`: Show this message and exit.

## `taskmn complete`

Flips the completion status of the indicated task

**Usage**:

```console
$ taskmn complete [OPTIONS] [TASK_ID]
```

**Arguments**:

* `[TASK_ID]`: The id of the task to change the completion status

**Options**:

* `--help`: Show this message and exit.

## `taskmn config`

Provides some configuration options

**Usage**:

```console
$ taskmn config [OPTIONS]
```

**Options**:

* `-m, --modify-path TEXT`: New Task Manager Store location ie [Drag_tasks.csv]
* `-s, --store-path`: Print the current Task store name
* `--help`: Show this message and exit.

## `taskmn delete`

Deletes the indicated task

**Usage**:

```console
$ taskmn delete [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: The id of the task to delete.  [required]

**Options**:

* `-f, --force`: Skip confirmation dialog
* `--help`: Show this message and exit.

## `taskmn docs`

Generate documentation

**Usage**:

```console
$ taskmn docs [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `generate`: Generate markdown version of usage...

### `taskmn docs generate`

Generate markdown version of usage documentation

**Usage**:

```console
$ taskmn docs generate [OPTIONS]
```

**Options**:

* `--name TEXT`: The name of the CLI program to use in docs.
* `--output FILE`: An output file to write docs to, like README.md.
* `--help`: Show this message and exit.

## `taskmn edit`

Edits the indicated task

**Usage**:

```console
$ taskmn edit [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: The id of the task to edit  [required]

**Options**:

* `-n, --name TEXT`: Name of the task
* `-desc, --description TEXT`: Description for the task
* `-dl, --deadline TEXT`: Deadline for the task (YYYY-MM-DD)
* `-p, --priority INTEGER RANGE`: Priority for the task  [0<=x<=2]
* `-f, --force`: Skip confirmation dialog
* `--help`: Show this message and exit.

## `taskmn init`

Creates the config file and the storage csv file whose name is provided

**Usage**:

```console
$ taskmn init [OPTIONS]
```

**Options**:

* `-s, --store-path TEXT`: [default: Drag_tasks.csv]
* `-e, --exist`: The file specified by -s already exists
* `--help`: Show this message and exit.

## `taskmn list`

Lists all the stored tasks in a pretty table.

**Usage**:

```console
$ taskmn list [OPTIONS]
```

**Options**:

* `-s, --sort TEXT`: How to sort the list [key/deadline/created/priority]  [default: key]
* `-r, --reverse`: Reverses the outputted list
* `--help`: Show this message and exit.

## `taskmn ls`

Alias for list

**Usage**:

```console
$ taskmn ls [OPTIONS]
```

**Options**:

* `-s, --sort TEXT`: How to sort the list [key/deadline/created/priority]  [default: key]
* `-r, --reverse`: Reverses the outputted list
* `--help`: Show this message and exit.

## `taskmn rm`

Alias for delete

**Usage**:

```console
$ taskmn rm [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: The id of the task to delete.  [required]

**Options**:

* `-f, --force`: Skip confirmation dialog
* `--help`: Show this message and exit.
