# clipboard/interface.py
import os
from typing import List
from .manager import ClipboardManager

class ClipboardManagerInterface(ClipboardManager):
    def __init__(self) -> None:
        super().__init__()

    # If you want to extend or override any method, do it here.
    # Otherwise, inherit behavior from ClipboardManager as is.
