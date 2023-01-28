from rich.traceback import install

from taskmn import __app_name__, task_manager_cli

"""
Entry point for Tasks Manager Cli
"""


def main():
    install(show_locals=True)
    task_manager_cli.app(prog_name=__app_name__)


if __name__ == "__main__":
    main()
