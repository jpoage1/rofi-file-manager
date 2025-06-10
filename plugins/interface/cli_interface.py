# plugins/interface/cli_interface.py
import logging 

interface_type = "stateful"
name = "cli"

def add_arguments(parser):
    pass

def run_cli_interface(manager):
    # This loop is primarily for non-socket (CLI) interfaces
    manager.main_loop()

def interface(config):
    return run_cli_interface(config)
