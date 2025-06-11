# plugins/interface/cli_interface.py
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
