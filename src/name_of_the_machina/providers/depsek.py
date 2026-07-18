# -*- coding: utf-8 -*-
# Python

"""Copyright (c) Alexander Fedotov.
This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.
"""
import urllib.request
import urllib.error
import json
from os import environ
from ..functions import *

api_key = environ.get("DEPSEK_API_KEY", '')
default_model = environ.get("DEPSEK_DEFAULT_MODEL", 'deepseek-v4-pro')
api_base = environ.get("DEPSEK_API_BASE", "https://api.deepseek.com")


# Set the mandatory headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "User-Agent": "depsek"
}


def get_function(func_name):
    # Look up tool by name in globals
    func = globals().get(func_name)
    # Look up in the caller frames
    if not func:
        import inspect
        frame = inspect.currentframe().f_back
        while frame:
            if func_name in frame.f_globals:
                func = frame.f_globals[func_name]
                break
            frame = frame.f_back
    return func


def query(payload):
    # Convert data dictionary to JSON and encode it to bytes
    data_bytes = json.dumps(payload).encode('utf-8')
    # Create the Request object
    req = urllib.request.Request(
        f'{api_base}/chat/completions',
        data=data_bytes,
        headers=headers,
        method="POST")
    # Try to query
    try:
        # Execute the request
        with urllib.request.urlopen(req, timeout=3000) as response:
            response_data = response.read().decode('utf-8')
            output = json.loads(response_data)
        return output

    except urllib.error.HTTPError as e:
        # Handle HTTP errors (e.g., 401 Unauthorized, 400 Bad Request)
        error_info = e.read().decode('utf-8', errors='ignore')
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Error Details: {error_info}")
        return {}

    except urllib.error.URLError as e:
        # Handle network/connection errors
        print(f"Failed to reach the server: {e.reason}")
        return {}


def respond(messages=None, instructions=None, tools=None, **kwargs):
    """ All parameters should be in kwargs, but they are optional
    """
    api_key = environ.get("DEPSEK_API_KEY", '')
    default_model = environ.get("DEPSEK_DEFAULT_MODEL", 'deepseek-v4-pro')
    api_base = environ.get("DEPSEK_API_BASE", "https://api.deepseek.com")

    # Set the mandatory headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Machina-Ratiocinatrix"
    }
    # Receive the instruction
    instruction = kwargs.get('system_instruction', instructions)
    first_message = [dict(role='system', content=instruction)] if instruction else []

    # add contents and user text to the first (instruction) message
    first_message.extend(messages)
    instruction_and_contents = first_message

    # Define the initial payload
    payload = {
        "model":            kwargs.get("model", default_model),
        "messages":         instruction_and_contents,
        "max_tokens":       kwargs.get("max_tokens", 132000),
        "reasoning_effort": "max",
    }
    # Tools if there are some
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = 'auto'

    complete_thoughts = ''

    while True:
        # Query the API
        result = query(payload)
        # id of the cached response can be here some day
        # response_id = result['id']
        completion_message = result['choices'][0]['message']
        instruction_and_contents.append(completion_message)
        thoughts = completion_message.get('reasoning_content', '')
        complete_thoughts += '\n\n' + thoughts + '\n\n'
        text = completion_message.get('content', '')
        function_calls = completion_message.get('tool_calls', [])

        if function_calls:
            # Call all requested functions and create response messages.
            for function_call in function_calls:
                call_id = function_call.get('id')
                func = function_call.get('function') # Old format of function.
                func_name = func.get('name')
                func_args_str = func.get('arguments', '{}')
                try:
                    if isinstance(func_args_str, str):
                        func_args = json.loads(func_args_str)
                    else:
                        func_args = func_args_str
                except Exception as e:
                    func_args = {}
                    print(f"Error parsing tool arguments for {func_name}: {e}")

                func = get_function(func_name)

                if func and callable(func):  # not a duplicate
                    try:
                        function_result = func(**func_args)
                        if isinstance(function_result, (dict, list)):
                            result = json.dumps(function_result)
                        else:
                            result = str(function_result)
                    except Exception as e:
                        result = f"Error executing tool {func_name}: {str(e)}"
                        print(result)
                else:
                    result = f"Error: Tool function {func_name} not found."
                    print(result)

                tool_message = {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result
                }
                # Add the response
                instruction_and_contents.append(tool_message)
        else:
            break
    return thoughts, text


if __name__ == "__main__":
    ...