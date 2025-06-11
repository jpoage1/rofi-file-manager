# plugins/cli_interface/cli_interface.py
import logging 
from core.plugin_base import InterfacePlugin

class CliInterface(InterfacePlugin):
    interface_type = "stateful"
    name = "cli"

    priority = 100

    @staticmethod
    def add_arguments(parser):
        pass

    @staticmethod
    def interface(manager):
        # This loop is primarily for non-socket (CLI) interfaces
        manager.main_loop()

    @staticmethod
    def available():
        """
        Checks if the CLI interface is available based on stdin being a TTY.
        """
        import sys
        is_tty = sys.stdin.isatty()
        if not is_tty:
            logging.warning("CliInterface not available: stdin is not an interactive terminal.")
        return is_tty
