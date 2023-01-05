from taskmn import __app_name__, TaskManagerCLI
from rich.traceback import install
"""
Entry point for Tasks Manager Cli
"""


def main():
    install(show_locals=True)
    TaskManagerCLI.app(prog_name=__app_name__)


if __name__ == "__main__":
    main()

