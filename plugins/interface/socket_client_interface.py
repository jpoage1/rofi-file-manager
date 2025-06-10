# plugins/interface/socket_client_interface.py
import socket
import json
import logging
import errno
import sys
import time

from menu_manager.payload import send_message, recv_message
from menu_manager.payload import get_timestamp

interface_type = "stateless"
name = "socket-client"

def add_arguments(parser):
    parser.add_argument("--host", default='127.0.0.1', help="Server host to connect to")
    parser.add_argument("--port", type=int, default=None, help="Server port to connect to")
    parser.add_argument("--timeout", type=float, default=5.0, help="Connection timeout in seconds")
    parser.add_argument("--retry-interval", type=float, default=0.05, help="Retry interval in seconds")

# def run_socket_client_interface(args):
#     from core.selector import selector
#     print(args)
#     frontend = args.frontend

#     start = time.time()
#     connected = False
#     while time.time() - start < args.timeout:
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 try:
#                     connected = True
#                     print(f"Client connecting to {args.host}:{args.port}")
#                     print(f"Client connecting at {get_timestamp()}")
#                     s.connect((args.host, args.port))
#                     # s.settimeout(args.timeout)
#                     print(f"Client connected at {get_timestamp()}")
#                     while True:
#                         data = recv_message(s, 'client')
#                         if not data:
#                             print("No data received, exiting")
#                             break
#                         args = json.loads(data)
#                         selection = selector(
#                             frontend, 
#                             args['entries'],
#                             args['prompt'],
#                             args['multi_select'],
#                             args['text_input']
#                         )
#                         send_message(s, json.dumps({"selection": selection}), 'client')

#                 except Exception as e:
#                     print(f"CLIENT ERROR: {e}", file=sys.stderr)
#                     # sys.exit(1) # Indicate failure
#                 finally:
#                     if 's' in locals():
#                         s.close()
#                 # End try
#             # End socket
#         except OSError as e:
#             if e.errno not in (errno.ECONNREFUSED, errno.EHOSTUNREACH):
#                 raise
#         time.sleep(args.retry_interval)
#     # End while    
#     if not connected:
#         raise TimeoutError(f"Server did not become ready at {host}:{port} within {timeout} seconds.")
#     sys.exit(0) # Indicate success

def interface(config):
    return run_socket_client_interface(config)

# def run_socket_client_interface(config):
#     host = config.host
#     port = config.port
#     timeout = config.timeout or 2.0
#     retry_interval = config.retry_interval or 0.05
#     frontend = config.frontend
#     selector = config.selector

#     start = time.time()
#     connected = False
#     while time.time() - start < timeout:
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 try:
#                     connected = True
#                     print(f"Client connecting to {host}:{port}")
#                     print(f"Client connecting at {get_timestamp()}")
#                     s.connect((host, port))
#                     print(f"Client connected at {get_timestamp()}")
#                     while True:
#                         data = recv_message(s, 'client')
#                         if not data:
#                             print("No data received, exiting")
#                             break
#                         args = json.loads(data)
#                         selection = selector(
#                             frontend, 
#                             args['entries'],
#                             args['prompt'],
#                             args['multi_select'],
#                             args['text_input']
#                         )
#                         send_message(s, json.dumps({"selection": selection}), 'client')
#                 except Exception as e:
#                     print(f"[Client] Error: {e}")
#         except OSError as e:
#             if e.errno not in (errno.ECONNREFUSED, errno.EHOSTUNREACH):
#                 raise
#         time.sleep(retry_interval)
#     if not connected:
#         raise TimeoutError(f"Server did not become ready at {host}:{port} within {timeout} seconds.")


def run_socket_client_interface(args):
    from core.selector import selector # Keep this import here as it's a function

    print(args) # Print the parsed arguments for debugging
    frontend = args.frontend # Get frontend from command-line args

    # Retrieve connection parameters from args, providing robust defaults
    host = args.host
    port = args.port
    # Use 2.0 as a default timeout if args.timeout is not set (e.g., None or 0)
    timeout = args.timeout if args.timeout is not None else 2.0
    # Use 0.05 as a default retry_interval if args.retry_interval is not set
    retry_interval = args.retry_interval if args.retry_interval is not None else 0.05

    start_time = time.time()
    connected = False
    s = None # Initialize socket variable outside the loop

    # --- Connection Retry Loop ---
    while time.time() - start_time < timeout:
        try:
            # Create a new socket for each connection attempt
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout) # Apply timeout to the socket operations
            
            print(f"Client: Attempting to connect to {host}:{port} at {get_timestamp()} (Time elapsed: {time.time() - start_time:.2f}s)")
            s.connect((host, port))
            print(f"Client: Connected to {host}:{port} at {get_timestamp()}")
            connected = True
            break # Connection successful, exit the retry loop

        except (OSError, socket.timeout) as e:
            # Catch specific connection errors that we want to retry on
            # and other socket.timeout errors during connect itself
            if isinstance(e, OSError) and e.errno in (errno.ECONNREFUSED, errno.EHOSTUNREACH):
                print(f"Client: Connection refused/unreachable by {host}:{port}. Retrying in {retry_interval:.2f}s... (Error: {e})", file=sys.stderr)
            elif isinstance(e, socket.timeout):
                 print(f"Client: Connection timed out to {host}:{port}. Retrying in {retry_interval:.2f}s... (Error: {e})", file=sys.stderr)
            else:
                # Re-raise for other OSErrors that are not connection-related (e.g., permissions)
                print(f"CLIENT ERROR: Unexpected OSError during connection attempt: {e}", file=sys.stderr)
                sys.exit(1) # Exit immediately for unexpected errors
            
            if s: # Close the socket if it was created and connect failed
                s.close()
            time.sleep(retry_interval) # Wait before the next retry
            
        except Exception as e:
            # Catch any other unexpected errors during the connection phase
            print(f"CLIENT UNEXPECTED ERROR during connection attempt: {e}", file=sys.stderr)
            sys.exit(1) # Indicate immediate failure for truly unexpected issues
    # End of connection retry loop

    # --- After Retry Loop: Check if connected or timeout ---
    if not connected:
        # If loop finished without connecting, raise TimeoutError or exit
        print(f"CLIENT ERROR: Server did not become ready at {host}:{port} within {timeout} seconds.", file=sys.stderr)
        # You can choose to raise TimeoutError here, or sys.exit(1)
        sys.exit(1) # Exit with failure status if connection failed after all retries

    # --- Communication Loop (only if connected successfully) ---
    try:
        while True:
            data = recv_message(s, 'client')
            if not data:
                print("Client: No data received, server disconnected or sent empty, exiting.")
                break # Server disconnected or sent empty message

            # CRITICAL FIX: Do NOT re-assign 'args' here.
            # 'args' holds your command-line arguments. The received data is a payload.
            received_payload = json.loads(data)

            selection = selector(
                frontend, # Use the original 'frontend' from command-line args
                received_payload['entries'],
                received_payload['prompt'],
                received_payload['multi_select'],
                received_payload['text_input']
            )
            send_message(s, json.dumps({"selection": selection}), 'client')

    except Exception as e:
        # Catch any errors during the communication phase
        print(f"CLIENT ERROR during communication: {e}", file=sys.stderr)
        sys.exit(1) # Indicate failure
    finally:
        if s: # Ensure socket is defined and closed
            s.close()
            print("Client: Socket closed.")
    sys.exit(0) # Indicate success after normal client operation
