# plugins/interface/cli_interface.py
import logging 
from core.plugin_base import SelectorPlugin


class CliSelector(SelectorPlugin):
    name = "cli"

    priority = 100

    @staticmethod
    def selector(entries, prompt, multi_select, text_input):
        """
        Handles user input via standard command-line input (input()).
        This is used for the 'cli' interface or as a fallback for socket-client
        if no graphical frontend is available/specified.
        Args:
            entries (list): List of menu options to display.
            prompt (str): The prompt string.
            multi_select (bool): True if multiple selections are allowed.
            text_input (bool): True if arbitrary text input is expected.
        Returns:
            list: A list containing the selected items, or ["QUIT_SIGNAL"].
        """
        logging.debug(f"[MenuManager.run_cli_selector] Using CLI selector: Prompt='{prompt}', Entries={entries}")
        try:
            print(f"\n{prompt}:")
            if entries:
                for i, entry in enumerate(entries):
                    print(f"  {i+1}. {entry}")
            else:
                print("(No options provided, enter text directly)")

            selected_input = input("Your choice: ").strip()

            if not selected_input:
                logging.info("[MenuManager.run_cli_selector] Empty input received from CLI. Simulating Quit.")
                return ["QUIT_SIGNAL"] # Treat empty input as a signal to quit/cancel

            # If it's primarily a text input prompt (and potentially no predefined entries)
            if text_input and not entries:
                return [selected_input]
            elif multi_select:
                # For CLI multi-select, assume comma-separated input
                return [s.strip() for s in selected_input.split(',') if s.strip()]
            else:
                # Try to convert to int for numbered options, otherwise assume direct string input
                try:
                    idx = int(selected_input) - 1
                    if 0 <= idx < len(entries):
                        return [entries[idx]]
                    else:
                        logging.warning(f"[MenuManager._run_cli_selector] Invalid numeric selection: '{selected_input}'.")
                        return [] # Return empty if invalid
                except ValueError:
                    # Not a number, treat as direct string input matching an entry
                    if selected_input in entries:
                        return [selected_input]
                    else:
                        logging.warning(f"[MenuManager._run_cli_selector] Invalid text selection: '{selected_input}'.")
                        return []

        except EOFError: # Handles Ctrl+D on stdin
            logging.info("[MenuManager._run_cli_selector] EOF received (Ctrl+D), simulating Quit.")
            return ["QUIT_SIGNAL"]
        except Exception as e:
            logging.error(f"[MenuManager._run_cli_selector] An unexpected error occurred in CLI selector: {e}")
            return ["QUIT_SIGNAL"]
