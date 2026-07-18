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


api_key = environ.get('META_API_KEY', '')  # meta_KEY', '')
api_base = environ.get('META_API_BASE', 'https://api.llama.com/v1')
content_model = environ.get('META_DEFAULT_CONTENT_MODEL', 'Llama-3.3-70B-Instruct')

# Set the mandatory headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "User-Agent": "Machina-Ratiocinatrix"
}


def get_weather(location):
    print(f"Executing weather tool for location: {location}")
    return {"temperature": "72F", "condition": "Sunny"}


def query(payload):
    # Convert data dictionary to JSON and encode it to bytes
    data_bytes = json.dumps(payload).encode('utf-8')

    # Create the Request object
    req = urllib.request.Request(
        f'{api_base}/chat/completions',
        data=data_bytes,
        headers=headers,
        method="POST")

    try:
        # Execute the request
        with urllib.request.urlopen(req, timeout=300) as response:
            response_data = response.read().decode('utf-8')
            response = json.loads(response_data)
            output = response['completion_message']
            # exit
            return output

    except urllib.error.HTTPError as e:
        # Handle HTTP errors (e.g., 401 Unauthorized, 400 Bad Request)
        error_info = e.read().decode('utf-8', errors='ignore')
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Error Details: {error_info}")
        return '', ''

    except urllib.error.URLError as e:
        # Handle network/connection errors
        print(f"Failed to reach the server: {e.reason}")
        return '', ''


def respond(messages=None, instructions=None, tools=None, **kwargs):
    """A continuation of text with a given context and instruction.
        kwargs:
            temperature     = 0 to 1.0
            top_p           = 0.0 to 1.0
            top_k           = The maximum number of tokens to consider when sampling.
            n               = 1 is mandatory for this method continuationS have n > 1
            max_tokens      = number of tokens
            stop            = ['stop']  array of up to 4 sequences
    """

    instruction = kwargs.get('system_instruction', instructions)
    first_message = [dict(role='system', content=instruction)] if instruction else []

    # add contents and user text to the first (instruction) message
    first_message.extend(messages)
    instruction_and_contents = first_message

    # Define the payload
    payload = {
        'model': kwargs.get('model', content_model),
        'messages': instruction_and_contents,
        # 'response_format': kwargs.get('response_format', {'type': 'text'}),
        'temperature': kwargs.get('temperature', 1.0),  # 0.0 to 1.0
        'max_completion_tokens': kwargs.get('max_tokens', 4028),
        'top_p': kwargs.get('top_p', 0.9),
        'top_k': kwargs.get('top_k', 10),
        'stream': False
    }
    # Tools if there are some
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = 'auto'

    while True:
        # Query the API
        completion_message = query(payload)
        content = completion_message.get('content','')
        text = content['text'] if content else ''
        tool_calls = completion_message.get('tool_calls', '')
        if tool_calls:
            instruction_and_contents.append(completion_message)
            for tool_call in tool_calls:
                tool_id = tool_call.get('id')
                func_info = tool_call.get('function', {})
                func_name = func_info.get('name')
                func_args_str = func_info.get('arguments', '{}')
                try:
                    if isinstance(func_args_str, str):
                        func_args = json.loads(func_args_str)
                    else:
                        func_args = func_args_str
                except Exception as e:
                    func_args = {}
                    print(f"Error parsing tool arguments for {func_name}: {e}")

                # Look up tool by name in globals and caller frames
                func = globals().get(func_name)
                # if not func:
                #     import inspect
                #     frame = inspect.currentframe().f_back
                #     while frame:
                #         if func_name in frame.f_globals:
                #             func = frame.f_globals[func_name]
                #             break
                #         frame = frame.f_back

                result = ""
                if func and callable(func):
                    try:
                        tool_result = func(**func_args)
                        if isinstance(tool_result, (dict, list)):
                            result = json.dumps(tool_result)
                        else:
                            result = str(tool_result)
                    except Exception as e:
                        result = f"Error executing tool {func_name}: {str(e)}"
                        print(result)
                else:
                    result = f"Error: Tool function {func_name} not found in scope."
                    print(result)

                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": func_name,
                    "content": result
                }
                instruction_and_contents.append(tool_message)
            continue
        # if it is not a tool call - just break
        else:
            break
    return '', text


if __name__ == '__main__':
    ...