import ast
import asyncio
import itertools
import os
import sys
import threading
import time
import warnings
from typing import Optional

from dotenv import load_dotenv
import re
import json
import pickle
import types

import openai
from openai import OpenAI
import anthropic
from colorama import Fore, Style
from pydantic import BaseModel

from load_env import openai_api_key, anthropic_api_key

# Load environment variables from the .env file
load_dotenv()

os.system('color')

openai_message_class = openai.types.chat.chat_completion.ChatCompletionMessage
openai_delta_type = openai.types.chat.chat_completion_chunk.ChoiceDelta
anthropic_message_class = anthropic.types.Message

# openai_api_key = os.getenv('OPENAI_API_KEY')
# anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

role_to_color = {
    "system": Fore.WHITE,
    "user": Fore.LIGHTGREEN_EX,
    "tool_options": Fore.CYAN,
    "assistant": Fore.LIGHTBLUE_EX,
    "tool": Fore.LIGHTCYAN_EX,
}

json_type_keyword_mappings = {
    'int': 'integer',
    'str': 'string',
    'float': 'number',
    'bool': 'boolean',
    'list': 'array',  # TODO: If 'list' type hints are typed out like 'list[str]', allow it to be a directly callable function
    # IMPORTANT: In Python, "array" is analogous to the list or tuple type, depending on usage. However, the json module in the Python standard library will always use Python lists to represent JSON arrays.
    'dict': 'object',  # TODO: If 'dict' type hints are typed out like 'dict[str, str]' where all the values are the same type, allow it to be a directly callable function
    # IMPORTANT: While Python dictionaries may use anything hashable as a key, in JSON all the keys must be strings.
    # Add more mappings as needed
}


class ActionLogEntryTypes:
    def __init__(self):
        self.ai_action = "ai_action"
        self.window_launched = "window_launched"
        self.window_closed = "window_closed"


actionLogEntryTypes = ActionLogEntryTypes()



def extract_code_blocks(text: str):
    pattern = re.compile(r'```(\w+)\n(.*?)```', re.DOTALL)
    matches = pattern.findall(text)
    language_identifier_index = 0
    code_index = 1
    return [(match[language_identifier_index], match[code_index].strip()) for match in matches]


def is_subscriptable(obj):
    return hasattr(obj, '__getitem__')


def get_message_role(message):
    if isinstance(message, dict):
        role = message.get('role')
    elif isinstance(message, openai_message_class):
        role = message.role
    elif isinstance(message, anthropic_message_class):
        role = message.role
    else:
        role = None
    return role


def get_message_content(message, verbose=False):  # TODO: Consider making a function of the LLM Client Wrapper Class
    if isinstance(message, dict):
        # User messages are formatted like this:
        #  Without images:
        #  {'role': 'user', 'content': ""}
        #  With images:
        #  {'role': 'user', 'content': [{"type": "text", "text": ""}, {"type": "image", ...}]}

        if verbose:
            print("\nMessage detected as a dict")

        content = message.get('content')

        # NOTE: Deprecated the following code for detecting an Anthropic content type due the changes needed to accommodate user messages with images
        #  If something breaks because of this, this section needs revisiting

        # if isinstance(content, list):
        #     if verbose:
        #         print("\nContent detected as an Anthropic content type")
        #     # Anthropic is unique
        #     # May need to modify function's output in the future to use appropriately.
        #     content = content[0].text
    elif isinstance(message, openai_message_class):
        if verbose:
            print("\nMessage detected as an OpenAI message type")
        content = message.content
    elif isinstance(message, anthropic_message_class):
        if verbose:
            print("\nMessage detected as an Anthropic message type")
        content = message.content[0].text
    else:
        content = None
    return content


def get_message_parsed_object(message, verbose=False):
    # TODO: Deprecate in favor of get_message_pydantic_output to handle refusals better
    parsed_object = None
    if isinstance(message, openai_message_class):
        if verbose:
            print("\nMessage detected as an OpenAI message type")
        parsed_object = message.parsed
    return parsed_object


def get_message_pydantic_output(message, api_provider='openai'):
    # If the model refuses to respond, you will get a refusal message
    if api_provider == 'openai':
        if message.refusal:
            return {'response_outcome': 'refusal', 'refusal_message': message.refusal}
        else:
            return {'response_outcome': 'parsed', 'pydantic_object': message.parsed}
    else:
        raise ValueError(f"api_provider \"{api_provider}\" is not supported")


def convert_response_message_to_context(message):
    if isinstance(message, openai_message_class):
        return message
    elif isinstance(message, anthropic_message_class):
        return {"role": "assistant", "content": message.content}
    return message


def pretty_print_text(text: str, color=Fore.WHITE, reset=True, end="", flush=False):
    print(color + text, end=end, flush=flush)
    if reset:
        print(Style.RESET_ALL, end="", flush=flush)


def repr_tool_call(function_name: str, function_args_json: str):
    return function_name + "(" + function_args_json.strip('{}') + ")"


def pretty_print_conversation(messages, verbose=False):
    print()  # New line
    for message in messages:
        role = get_message_role(message)
        content = get_message_content(message, verbose)
        if isinstance(content, list):
            content_text = ""
            num_images = 0
            for content_item_index, content_item in enumerate(content):
                if isinstance(content_item, dict):
                    content_item_type = content_item.get('type')
                    if content_item_type == 'text':
                        content_item_text = content_item.get('text')
                        if isinstance(content_item_text, str):
                            content_text += content_item_text
                            if content_item_index != len(content) - 1:
                                content_text += "\n"  # Add a new line if not the last content item
                    elif content_item_type == 'image' or content_item_type == 'image_url':
                        num_images += 1
                        content_text += f"{{image_{num_images}}}\n"
            content = content_text

        # If role is system, user, or tool then treat as a dictionary
        if role == "system":
            print(role_to_color[role] + "system: \t" + "\n\t\t\t".join(content.split("\n")) + "\n")
        elif role == "user":
            print(role_to_color[role] + "user: \t\t" + "\n\t\t\t".join(content.split("\n")) + "\n")
        elif role == "tool":
            print(role_to_color[role] + "tool: \t\t" + message['name'] + "() ->\n\n" + "\t\t\t" + "\n\t\t\t".join(
                content.split("\n")) + "\n")
        # If role is assistant then treat as an ChatCompletionMessage object
        elif role == "assistant":
            if content:
                print(role_to_color[role] + "assistant: \t" + "\n\t\t\t".join(content.split("\n")))
            else:
                print(role_to_color[role] + "assistant: \t" + "None")
            if isinstance(message, openai_message_class):
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        print(
                            role_to_color[role] +
                            "tool_call: \t" +
                            repr_tool_call(tool_call.function.name, tool_call.function.arguments)
                        )
            print()
        print(Style.RESET_ALL)


def pretty_print_tool_options(tool_options: list, api_provider: str = 'openai'):
    tool_options_str = "\n"
    if api_provider == 'openai':
        for n, tool in enumerate(tool_options):
            if n != 0:
                tool_options_str += "\n"
            tool_options_str += f"- {tool['function']['name']}"
            if tool['function'].get('parameters'):
                if properties := tool['function']['parameters'].get('properties'):
                    for i, property_name in enumerate(properties.keys()):
                        if i == 0:
                            tool_options_str += ":\n\t"
                            tool_options_str += f"{property_name}"
                        else:
                            tool_options_str += f", {property_name}"
    else:
        raise ValueError(f"api_provider value '{api_provider}' not supported")

    print("\n" + role_to_color['tool_options'] + "tool_options: \t" + "\n\t\t\t".join(tool_options_str.split("\n")) + "\n")
    print(Style.RESET_ALL)


# # Old Version (Does not filter for "wait", "fail", and "done" actions. Also fails to filter procedural code for windows that close then open again due to accessibility glitches)
# def write_procedural_code_from_action_log(sequential_action_log):
#     pseudocode = ""
#     actual_code = ""
#     for action in sequential_action_log:
#         if action.get('type') == actionLogEntryTypes.ai_action:
#             log = action['entry']
#             code_line = log['code_line']
#             pseudocode_line = log['pseudocode_line']
#             pseudocode += pseudocode_line
#             actual_code += code_line
#         elif action.get('type') == actionLogEntryTypes.window_closed:
#             log = action['entry']
#             line = f"\n# Detected Window Closed: {construct_window_text(log['executable'], log['window_name'], log['handle'])}"
#             pseudocode += line
#             actual_code += line
#         elif action.get('type') == actionLogEntryTypes.window_launched:
#             log = action['entry']
#             line = f"\n# Detected Window Launch: {construct_window_text(log['executable'], log['window_name'], log['handle'])}"
#             pseudocode += line
#             actual_code += line
#     return pseudocode, actual_code


def compile_open_handles_from_action_log(action_log, verbose=False):
    # Create list of handles for windows interacted with or launched by the Action Agent that remain open
    open_handles_of_interest = set()
    pre_existing_handles_closed = set()
    for action in action_log:
        if action['type'] == actionLogEntryTypes.ai_action:
            handle = action['entry']['function_args'].get('handle')
            if handle:
                open_handles_of_interest.add(handle)
        elif action['type'] == actionLogEntryTypes.window_closed:
            handle = action['entry'].get('handle')
            if handle:
                if handle in open_handles_of_interest:
                    open_handles_of_interest.discard(handle)
                else:
                    pre_existing_handles_closed.add(handle)
        elif action['type'] == actionLogEntryTypes.window_launched:
            handle = action['entry'].get('handle')
            if handle:
                if handle in pre_existing_handles_closed:
                    pre_existing_handles_closed.discard(handle)
                else:
                    open_handles_of_interest.add(handle)
    if verbose:
        print(f"Pre-existing windows closed: {pre_existing_handles_closed}")
    # Return screenshots of those windows
    return open_handles_of_interest


def user_prompt_to_message(prompt: str, base64_images: list[dict] = None, api_provider: str = 'anthropic') -> dict:  # TODO: Make a method of the llm client wrapper class
    """
    Converts a prompt into a message appendable to the user-assistant context list.
    NOTE: Sending images is only supported by the Anthropic Completions API at this time

    Args:
        prompt (str): textual prompt to send to LLM
        base64_images: e.g. [{"media_type": "image/png", "image_data": img_base64}]
        api_provider: 'openai' or 'anthropic'

    Returns: Message dictionary

    """
    if base64_images is None:
        return {'role': 'user', 'content': prompt}

    elif not isinstance(base64_images, list):
        raise ValueError("Parameter 'images' must be of type 'list'")

    user_message = {'role': 'user', 'content': []}

    if api_provider == 'anthropic':
        if len(base64_images) == 1:
            base64_image = base64_images[0]
            user_message['content'].append(
                [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': base64_image['media_type'],
                            'data': base64_image['image_data']
                        }
                    }
                ]
            )

        else:
            for i, base64_image in enumerate(base64_images):
                user_message['content'].extend(
                    [
                        {"type": "text", "text": f"Image {i+1}:"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": base64_image['media_type'],
                                "data": base64_image['image_data'],
                            },
                        }
                    ]
                )

        user_message['content'].append({'type': 'text', 'text': prompt})

    elif api_provider == 'openai':
        user_message['content'].append({'type': 'text', 'text': prompt})
        for i, base64_image in enumerate(base64_images):
            user_message['content'].append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{base64_image['media_type']};base64,{base64_image['image_data']}"}
                }   # TODO: Test
            )

    return user_message



def fabricated_assistant_response(content):
    return {'role': 'assistant', 'content': content}


# def get_function_name_from_code_block_str(code_block: str):
#     """
#     Args:
#         code_block (str): string containing a function definition at the very beginning
#     Returns:
#         function_name (str)
#     """
#
#     # Regular expression to match the function name
#     pattern = r'def\s+(\w+)\s*\('
#
#     # Search for the pattern in the text
#     match = re.search(pattern, code_block)
#
#     # Extract and print the function name
#     if match:
#         function_name = match.group(1)
#         return function_name
#     else:
#         return None


def load_pickle_file(filepath, default=None, verbose=False):
    if not os.path.exists(filepath):
        # If the file does not exist, create it and return the default value
        with open(filepath, 'wb') as file:
            pickle.dump(default, file)
        if verbose:
            print(f"File '{filepath}' does not exist, creating file with default value")
        return default

    if os.path.getsize(filepath) > 0:
        # If the file is not empty...
        with open(filepath, 'rb') as file:
            return pickle.load(file)
    else:
        # If the file is empty...
        if verbose:
            print("File is empty, returning default value")
        return default


def load_json_file(filepath, default=None, verbose=False):
    if not os.path.exists(filepath):
        # If the file does not exist, create it and return the default value
        with open(filepath, 'w') as file:
            json.dump(default, file)
        if verbose:
            print(f"File '{filepath}' does not exist, creating file with default value")
        return default

    if os.path.getsize(filepath) > 0:
        # If the file is not empty...
        with open(filepath, 'r') as file:
            return json.load(file)
    else:
        # If the file is empty...
        if verbose:
            print("File is empty, returning default value")
        return default


def reorder_skills_list(skills, verbose=False):
    new_skill_names = [skill['function_name'] for skill in skills]
    helper_functions_array = [skill['helper_function_references'] for skill in skills]

    # Create dictionary of skills that rely on other proposed skills in the same batch
    batch_dependencies = {}
    for i, helper_functions in enumerate(helper_functions_array):
        # Get subset of helper functions for each proposed skill that only includes methods in the new batch
        stack = [helper for helper in helper_functions if helper in new_skill_names]
        # Add subset to the new helper functions array
        batch_dependencies[new_skill_names[i]] = stack

    # Re-order skills_to_add so helper function definitions come before function definitions they're called in
    reordered_skills = []
    visited = set()
    recursion_stack = set()

    # Method for topological sorting using depth-first search (DFS)
    def dfs(function_name):
        if function_name in recursion_stack:
            raise ValueError(f"Circular dependency detected involving skill: {function_name}")

        if function_name in visited:
            return

        visited.add(function_name)
        recursion_stack.add(function_name)

        for dependency in batch_dependencies.get(function_name, []):
            dfs(dependency)

        recursion_stack.remove(function_name)
        reordered_skills.append(next(skill for skill in skills if skill['function_name'] == function_name))

    try:
        for skill_node in skills:
            skill_name = skill_node['function_name']
            if skill_name not in visited:
                dfs(skill_name)

        # Replace the original skills list with the reordered list
        skills = reordered_skills
        if verbose:
            print("Topological sort of skills list successful.")
            print(reordered_skills)
        return skills
    except ValueError as e:
        if verbose:
            print(f"Error: {e}")
            print("Unable to complete topological sort of skills due to circular function call dependencies.")
        return


def add_parameter_to_tool_definition(name: str, description: str, json_type: str, tool: dict, mandatory: bool = True, api_provider: str = "openai"):
    if json_type not in json_type_keyword_mappings.values():
        raise ValueError(f"{repr(json_type)} is not a valid json_type")
    elif json_type == 'array' or json_type == 'object':
        raise ValueError(f"The <array> and <object> types are not supported as parameters")

    if api_provider == 'openai':
        structured_outputs = False
        # Detect if strict is set to True in the tool definition
        if tool['function'].get("strict") is True:
            structured_outputs = True

        # Add the new parameter to the OpenAI tool definition
        if name not in tool['function']['parameters']['properties']:
            if structured_outputs:
                tool['function']['parameters']['required'].append(name)
                if mandatory:
                    tool['function']['parameters']['properties'][name] = {"type": json_type, "description": description}
                else:
                    tool['function']['parameters']['properties'][name] = {"type": [json_type, "null"], "description": description}
            else:
                tool['function']['parameters']['properties'][name] = {"type": json_type, "description": description}
                if mandatory:
                    tool['function']['parameters']['required'].append(name)
        else:
            raise ValueError(f"Name \"{name}\" conflicts with an existing parameter in the {tool['function']['name']} tool")
    else:
        raise ValueError(f"api_provider argument {repr(api_provider)} not yet supported by make_comment_arg_required()")


def make_comment_arg_required(skill_tool: dict, api_provider: str, structured_outputs=True):
    """Modifies the tool definition of a skill by making the `comment` arg a required parameter"""
    if api_provider == 'openai':
        if "comment" in skill_tool['function']['parameters']['properties']:
            if structured_outputs:
                arg_type = skill_tool['function']['parameters']['properties']['comment'].get('type')
                if isinstance(arg_type, list):
                    if "null" in arg_type:
                        skill_tool['function']['parameters']['properties']['comment']['type'].remove('null')
            else:
                if "comment" not in skill_tool['function']['parameters']['required']:
                    skill_tool['function']['parameters']['required'].append("comment")
    else:
        raise ValueError(f"api_provider argument {repr(api_provider)} not supported by make_comment_arg_required()")


def get_client_wrapper_for_llm_api_provider(model_api_provider):
    # Get the key for the correct tools list in bedrock_tools
    if model_api_provider == 'openai':
        return OpenAIClientWrapper(api_key=openai_api_key)
    elif model_api_provider == 'anthropic':
        return AnthropicClientWrapper(api_key=anthropic_api_key)
    else:
        raise ValueError("ActionAgent's self.model_api_provider does not have a valid value")


def sanitize_function_response(function_response):
    # Create a string function response if one is not returned by the method
    if not function_response:
        return "The function was executed. A new UI state may still be loading."
    elif not isinstance(function_response, str):
        return repr(function_response)
    return function_response


def sanitize_filepath_string(input_string):
    # Step 1: Replace double quotes with single quotes
    sanitized = input_string.replace('"', "'")

    # Step 2: Remove all punctuation except single quotes
    allowed_punctuation = '\''
    sanitized = ''.join(char for char in sanitized if
                        char.isalnum() or char in allowed_punctuation or char.isspace())

    # Step 3: Make all text lowercase
    sanitized = sanitized.lower()

    # Step 4: Replace blank space with underscores
    sanitized = sanitized.replace(' ', '_')

    # Step 5: Return the sanitized string
    return sanitized


def make_unique_filepath(filepath):
    base, ext = os.path.splitext(filepath)  # Split the file into base and extension
    counter = 1

    # Check if the file already exists
    while os.path.exists(filepath):
        filepath = f"{base}_{counter}{ext}"  # Append a counter to the base name
        counter += 1

    return filepath


def generate_numbered_plan_from_steps(steps: list[str], str_header="Plan:"):
    # Process list of steps into a numbered string
    numbered_string = "\n"
    if str_header:
        numbered_string += (str_header + "\n")
    for i, list_item in enumerate(steps, start=1):
        numbered_string += f"{i}) {list_item}\n"
    return numbered_string


def format_strings_as_numbered_checklist(str_list: list[str], current_index: int, start_index: int = 0, end_index: int = None):
    # Process list of steps into a numbered string
    if end_index is None:
        end_index = len(str_list) - 1
    if start_index >= len(str_list) or start_index < 0:
        raise ValueError("start_index is out of bounds of list 'steps'")
    if end_index >= len(str_list) or end_index < 0:
        raise ValueError("end_index is out of bounds of list 'steps'")
    if end_index < start_index:
        raise ValueError("end_index cannot be less than start_index")
    if current_index > end_index or current_index < start_index:
        raise ValueError("(start_index <= current_index <= end_index) must hold")

    annotated_plan = ""
    for i, list_item in enumerate(str_list[start_index:end_index + 1], start=start_index):
        if i == current_index:
            annotated_plan += "-->"  # Pointer for current step

        annotated_plan += (f"\t{i+1}) "  # Step number
                           f"[{'x' if i < current_index else ' '}] "  # Markdown-style checkbox
                           f"{list_item}\n"  # Step item
                           )

    if end_index < len(str_list) - 1:
        annotated_plan += "\t...\n"

    annotated_plan += "\n"
    return annotated_plan


def async_to_sync_generator(agen):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while True:
            item = loop.run_until_complete(agen.__anext__())
            if isinstance(item, AsyncReturnObject):
                # If an AsyncReturnObject is yielded, return the "return_value" attribute
                return item.return_value
            yield item
    except StopAsyncIteration:
        pass
    finally:
        loop.close()


class ConversationDelta(BaseModel):
    role: str = "callout"  # role can be "callout" or "assistant_chunk"
    content: str = ""
    spinner_action: Optional[str] = None  # spinner_action can be "start", "stop", or None


class AsyncReturnObject:
    def __init__(self, return_value):
        self.return_value = return_value


# TODO: LLM Client Wrapper superclass
class LLMClientWrapper:
    pass


class OpenAIClientWrapper:
    # Wrapper for OpenAI ChatCompletions API
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.message_type = openai_message_class
        self.delta_type = openai_delta_type
        self.spinner_running = False
        self.last_tool_call_comments = ""
        self.last_message_role = ""

    def embed(self, model, text_to_embed):
        text_embedding = None
        try:
            text_embedding = self.client.embeddings.create(input=text_to_embed, model=model).data[0].embedding
        except Exception as e:
            print("Unable to generate OpenAI embedding")
            print(f"Exception: {e}")
        finally:
            return text_embedding

    def query(self, model, context, response_format=None, temperature=1.0, tools=None, tool_choice=None,
              parallel_tool_calls=True, prediction=None, reasoning_effort=None, verbose=False):
        if response_format == "text":
            response_format = None
        if isinstance(response_format, str):
            response_format = {"type": response_format}

        query_args = {
            "model": model,
            "messages": context,
        }

        if temperature:
            query_args["temperature"] = temperature
        if response_format:
            query_args["response_format"] = response_format
        if tools:
            query_args["tools"] = tools
            query_args["tool_choice"] = tool_choice
            query_args["parallel_tool_calls"] = parallel_tool_calls
        if prediction:
            if tools:
                raise ValueError("'tools' parameter is not supported with predictive responses.")
            if response_format:
                raise ValueError("'response_format' parameter with value other than \"text\" or None is not supported with predictive responses.")
            query_args["prediction"] = {"type": "content", "content": prediction}
        if reasoning_effort:
            query_args["reasoning_effort"] = reasoning_effort

        completion = self.client.chat.completions.create(**query_args)

        response_message = completion.choices[0].message

        return response_message  # returns ChatCompletionMessage object

    def stream_query(self, model, context, response_format="text", temperature=1.0, tools=None, tool_choice=None,
                     parallel_tool_calls=True, verbose=False):

        if isinstance(response_format, str):
            response_format = {"type": response_format}
        query_args = {
            "model": model,
            "messages": context,
            "response_format": response_format,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            query_args["tools"] = tools
            query_args["tool_choice"] = tool_choice
            query_args["parallel_tool_calls"] = parallel_tool_calls

        stream = self.client.chat.completions.create(**query_args)

        for chunk in stream:
            yield chunk

        response_content = ""

        # Loop through the stream of responses
        for chunk in stream:
            chunk_content = chunk.choices[0].delta.content
            if chunk_content is not None:
                yield chunk_content
                response_content += chunk_content  # Append content from each delta

        return response_content, stream  # returns

    def print_delta(self, delta_role: str, delta_content: str):
        # print(f"new delta: {repr(delta_content)}", end="")
        if delta_role == "callout":
            if self.last_message_role == "assistant_chunk" or self.last_message_role == "assistant":
                print()
            pretty_print_text(delta_content, color=Fore.LIGHTCYAN_EX, end="")
            self.last_message_role = delta_role

        elif delta_role == "assistant_chunk" or delta_role == "assistant":
            pretty_print_text(delta_content, color=Fore.LIGHTBLUE_EX, end="", flush=True)
            self.last_message_role = delta_role

    def circle_spinner_display(self):
        spinner = itertools.cycle(["◐", "◓", "◑", "◒"])  # Characters for circle spinner
        sys.stdout.write(next(spinner)+" ")
        while self.spinner_running:
            sys.stdout.write(f'\b\b{next(spinner)} ')
            sys.stdout.flush()
            time.sleep(0.1)

    def domino_spinner_display(self):
        spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])  # Characters for domino spinner
        sys.stdout.write(next(spinner)+" ")
        while self.spinner_running:
            sys.stdout.write(f'\b\b{next(spinner)} ')
            sys.stdout.flush()
            time.sleep(0.1)

    def capture_streamed_assistant_response_spinner(self, delta_stream, print_response_stream=True):
        if isinstance(delta_stream, types.GeneratorType):
            spinner_thread = None
            content_with_active_spinner = False
            while True:
                try:
                    delta = next(delta_stream)  # Capture next value yielded by the generator
                    if print_response_stream:
                        if delta.spinner_action == "start":
                            if self.spinner_running:
                                warnings.warn("Spinner already running")
                                # Stop the spinner
                                self.spinner_running = False
                                if spinner_thread is not None:
                                    spinner_thread.join()  # Wait for the spinner to stop
                                    sys.stdout.write('\b\b')
                                    sys.stdout.flush()

                            # Print the starting message first without creating new line
                            delta_content = delta.content
                            if delta_content:
                                content_with_active_spinner = True
                            self.print_delta(delta.role, delta_content)

                            # Start the spinner on the same line in a separate thread
                            self.spinner_running = True
                            if content_with_active_spinner:
                                spinner_thread = threading.Thread(target=self.domino_spinner_display)
                            else:
                                spinner_thread = threading.Thread(target=self.circle_spinner_display)
                            spinner_thread.daemon = True
                            spinner_thread.start()

                        elif delta.spinner_action == "stop":
                            # Stop the spinner
                            self.spinner_running = False
                            if spinner_thread is not None:
                                spinner_thread.join()  # Wait for the spinner to stop
                                sys.stdout.write('\b\b')  # Clear the spinner character
                                sys.stdout.flush()

                            if content_with_active_spinner or delta.content:
                                # Output a delta.content plus a new line after cancelling the spinner
                                delta_content = delta.content
                                if delta.role != "assistant_chunk":
                                    delta_content += '\n'
                                self.print_delta(delta.role, delta_content)
                                content_with_active_spinner = False
                            else:
                                pass

                        else:
                            if self.spinner_running:
                                warnings.warn("Spinner still running!")
                                # Stop the spinner
                                self.spinner_running = False
                                if spinner_thread is not None:
                                    spinner_thread.join()  # Wait for the spinner to stop
                                    sys.stdout.write('\b\b')
                                    sys.stdout.flush()

                            delta_content = delta.content
                            if delta.role != "assistant_chunk":
                                delta_content += '\n'
                            self.print_delta(delta.role, delta_content)

                except StopIteration as e:
                    return_value = e.value  # Capture the final result of the generator
                    break  # Exit the loop

        else:
            return_value = delta_stream

        return return_value

    def capture_streamed_assistant_response(self, delta_stream, print_response_stream=True):
        if isinstance(delta_stream, types.GeneratorType):
            while True:
                try:
                    delta = next(delta_stream)  # Capture next value yielded by the generator
                    if print_response_stream:
                        self.print_delta(delta.role, delta.content)

                except StopIteration as e:
                    return_value = e.value  # Capture the final result of the generator
                    break  # Exit the loop

        else:
            return_value = delta_stream

        return return_value

    def query_with_schema(self, model, context, response_format, temperature=1.0, tools=None, tool_choice=None,
                          parallel_tool_calls=True, verbose=False):
        """
        Query method for structured outputs
        """

        query_args = {
            "model": model,
            "messages": context,
            "response_format": response_format,  # Pydantic object
            "temperature": temperature
        }

        if tools:
            query_args["tools"] = tools
            query_args["parallel_tool_calls"] = parallel_tool_calls  # Specify whether to limit output to maximum one function call at a time
            if tool_choice:
                query_args["tool_choice"] = tool_choice

        completion = self.client.beta.chat.completions.parse(**query_args)

        response_message = completion.choices[0].message

        if verbose:
            if response_message.refusal:
                print("OpenAI model refused to respond to query.")
                print(response_message.refusal)
            elif hasattr(response_message, "tool_calls"):
                if response_message.tool_calls is not None:
                    print(f"OpenAI model called a tool: {response_message.tool_calls[0].function}")
            elif response_message.parsed:
                print("OpenAI model successfully returned a parsed object.")

        return response_message

    def get_tool_name_from_definition(self, tool_def: dict):
        return tool_def["function"]["name"]

    def get_tool_args_from_definition(self, tool_def: dict):
        parameters = tool_def["function"].get("parameters")
        if parameters:
            return parameters.get("properties")
        return None

    def get_tool_calls(self, tool_call_message):
        if tool_call_message.tool_calls:
            return tool_call_message.tool_calls
        return

    def get_names_of_tools_called(self, tool_call_message):
        tool_call_names = []
        if tool_call_message.tool_calls:
            for tool_call in tool_call_message.tool_calls:
                tool_call_names.append(tool_call.function.name)
        return tool_call_names

    def get_name_from_tool_call(self, tool_call) -> str:
        return tool_call.function.name

    def get_arguments_json_from_tool_call(self, tool_call) -> str:
        return tool_call.function.arguments

    def get_arguments_from_tool_call(self, tool_call) -> dict:
        return json.loads(self.get_arguments_json_from_tool_call(tool_call))

    def get_id_from_tool_call(self, tool_call):
        return tool_call.id

    def format_skills_as_info_string(self, skills: list, indent=None):
        skill_info = [
            {
                "function_name": skill_node["function_name"],
                "description": skill_node["summary"]
            } for skill_node in skills
        ]
        if indent is None:
            return json.dumps(skill_info)
        else:
            return json.dumps(skill_info, indent=indent)

    def create_tool_response_message(self, tool_call_id, function_name: str, function_response: str):
        return {
            "tool_call_id": tool_call_id,
            "role": "tool",
            "name": function_name,
            "content": function_response,
        }

    def create_failed_tool_call_response(self, tool_call, error: Exception):
        content = f"{tool_call.function.name}() failed. Error: {error}"
        tool_failure_response = self.create_tool_response_message(
            tool_call_id=tool_call.id,
            function_name=tool_call.function.name,
            function_response=content
        )
        return tool_failure_response

    def run_tool_call(self, tool_call_id, function_name: str, function_args: dict, available_functions: dict,
                      step: str = None, verbose=False, **kwargs):
        # Check if the function is in available_functions keys
        if function_to_call := available_functions.get(function_name):
            # Save comments
            self.last_tool_call_comments = function_args.get('comment', '') + '\n'

            # Check if the function is a bedrock skill
            if function_name in ['click_element', 'type_field', 'execute_hotkey', 'wait', 'fail', 'done']:
                # Add `window_trees` and `verbose` to the arguments dictionary since these variables won't be included in the agent's JSON response
                function_args['window_trees'] = kwargs.get('window_trees')
                function_args['verbose'] = verbose

                if verbose:
                    print("Function Args:", function_args)

                # TODO: Deal with Exceptions

                # TODO: If either a bedrock or skill library tool call throws an error, trigger a mechanism
                #  that will prevent a new skill from being added to the skill library

                # Run the bedrock function and get response
                function_response, pseudocode_line, code_line, warning = function_to_call(
                    function_name,
                    **function_args
                )  # NOTE: function_response must be a string

                if verbose:
                    print(f"{function_name}() ran without raising an error.")

                action_log_entry = {
                    "type": actionLogEntryTypes.ai_action,
                    "entry": {
                        "function": function_name,
                        "function_args": {k: v for k, v in function_args.items() if k != 'window_trees'},
                        "pseudocode_line": pseudocode_line,
                        "code_line": code_line,
                    }
                }
                if warning:
                    action_log_entry['entry']['warning'] = warning
                if step:
                    action_log_entry['entry']['step'] = step

            else:
                if verbose:
                    print("Function Args:", function_args)

                function_response = function_to_call(**function_args)  # TODO: Skill return values not presently sanitized for the Action Agent or Conversation Manager Agent. Solution -> instruct Skill Processor Agent to return a dictionary where one of the keys is the return value to the agent that called it.
                # TODO: Deal with Exceptions

                if verbose:
                    print(f"{function_name}() succeeded")

                function_response = sanitize_function_response(function_response)

                code_line = f"\n{function_name}("
                pseudocode_line = f"\n{function_name}("
                for count, (key, value) in enumerate(function_args.items()):
                    if key not in ['comment']:  # List of args to exclude in the code and pseudocode
                        if count > 0:
                            # Insert a comma and a space if the argument is not the first
                            code_line += ", "
                            pseudocode_line += ", "
                        if type(value) == str:
                            code_line += f"{key}={repr(value)}"
                            pseudocode_line += f"{key}={repr(value)}"
                        else:
                            code_line += f"{key}={value}"
                            pseudocode_line += f"{key}={value}"
                code_line += ")"
                pseudocode_line += ")"
                if function_args.get('comment') is not None:
                    code_line += f"  # {function_args['comment']}"
                    pseudocode_line += f"  # {function_args['comment']}"

                action_log_entry = {
                    "type": actionLogEntryTypes.ai_action,
                    "entry": {
                        "function": function_name,
                        "function_args": {k: v for k, v in function_args.items() if k != 'window_trees'},
                        "pseudocode_line": pseudocode_line,
                        "code_line": code_line,
                    }
                }
                if step:
                    action_log_entry['entry']['step'] = step

        else:
            # For the scenario where a tool call is made to a function that doesn't exist
            function_response = f"Error running tool call: {function_name} does not exist as an available tool."
            raise ValueError(function_response)

        # Add the function's response to `tool_messages` with which to extend user-agent conversation
        tool_message = {
            "name": function_name,
            "arguments": function_args,
            "tool_response": self.create_tool_response_message(
                tool_call_id=tool_call_id,
                function_name=function_name,
                function_response=function_response
            )
        }

        return action_log_entry, tool_message

    def run_tool_calls(self, tool_call_info: list[dict[str, str, str]], available_functions: {}, verbose=False, **kwargs):
        # Anticipates tool_call_info as [{"tool_call_id": "id", "function_name": "my_function", "function_args": "function_args_json"}]
        action_log_entries = [None] * len(tool_call_info)
        tool_messages = [None] * len(tool_call_info)

        for i, tool_call in enumerate(tool_call_info):
            if verbose:
                print(f"\nTool Call Name: {repr(tool_call['function_name'])}")
                print(f"Tool Call Args: {repr(tool_call['function_args'])}")
            tool_call_id = tool_call['tool_call_id']
            function_name = tool_call['function_name']
            function_args = json.loads(tool_call['function_args'])

            action_log_entries[i], tool_messages[i] = (
                self.run_tool_call(tool_call_id, function_name, function_args, available_functions, verbose=verbose, **kwargs)
            )

        return action_log_entries, tool_messages

    def run_tool_calls_in_message(self, tool_call_bearing_message, available_functions: {}, verbose=False, **kwargs):
        """
        Runs OpenAI tool calls

        Args:
            tool_call_bearing_message: Response message from OpenAI model containing tool_calls
            available_functions (dict): Dictionary of functions made available to the tool
            verbose: Controls method print verbosity
            **kwargs: Other arguments (such as window_trees) needed to run the function not included in the tool call

        Returns:
            action_log_entries: Array of log entries for the completed action
            tool_messages: Array of tool response messages

        """

        # Check that the message is a valid object for this wrapper
        if type(tool_call_bearing_message) != self.message_type:
            raise ValueError("Expected tool call message to be an OpenAI response message with a tool call")

        action_log_entries = None
        tool_messages = None

        tool_calls = tool_call_bearing_message.tool_calls
        if tool_calls:
            action_log_entries = [None] * len(tool_calls)
            tool_messages = [None] * len(tool_calls)
            for i, tool_call in enumerate(tool_calls):
                tool_call_id = tool_call.id
                function_name = tool_call.function.name
                if verbose:
                    print(f"\nTool Call Name: {repr(function_name)}")
                    print("Tool Call Args: " + repr(tool_call.function.arguments))
                function_args = json.loads(tool_call.function.arguments)

                action_log_entries[i], tool_messages[i] = (
                    self.run_tool_call(tool_call_id, function_name, function_args, available_functions, verbose=verbose, **kwargs)
                )

        return action_log_entries, tool_messages

    def run_streamed_tool_call(self, tool_call, tool_name: str, tool_args_accumulator: str, available_functions: dict, verbose=False, **kwargs) -> []:
        """
        Runs OpenAI tool calls

        Args:
            tool_call: OpenAI tool call object
            tool_name (str): Name of the function
            tool_args_accumulator (str): JSON string containing the function arguments, concatenated as they are received in chunks from the AI model
            available_functions (dict): Dictionary of functions made available to the tool
            verbose: Controls method print verbosity
            **kwargs: Other arguments (such as window_trees) needed to run the function not included in the tool call

        Returns:
            action_log_entries: Array of log entries for the completed action
            tool_messages: Array of tool response messages

        """

        if verbose:
            print(f"function_name: {tool_name}", flush=True)
            print(f"function_args: {repr(tool_args_accumulator)}", flush=True)
        function_args = json.loads(tool_args_accumulator)

        if function_to_call := available_functions.get(tool_name):
            function_response = function_to_call(**function_args)  # TODO: Not yet built to handle bedrocks. Not sure if this is needed
            tool_response_message = self.create_tool_response_message(
                tool_call_id=tool_call.id,
                function_name=tool_call.function.name,
                function_response=function_response
            )
            return tool_response_message


class AnthropicClientWrapper:
    # Wrapper for Anthropic Messages API
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.message_type = anthropic_message_class

    def query(self, model, context, max_tokens: int = 2048, temperature=None, tool_choice=None, tools: dict = None):
        # Returns LLM response message from query

        if not tools:
            tool_choice = None

        # Anthropic Messages API requires the system prompt as an argument rather than as a list item in messages with a "system" role
        system_prompt = None
        if context[0]['role'] == 'system':
            system_prompt = context[0]['content']
            context = context[1:]

        anthropic_message_creation_kwargs = {'model': model, 'messages': context, 'max_tokens': max_tokens}
        if temperature:
            anthropic_message_creation_kwargs['temperature'] = temperature
        if system_prompt:
            anthropic_message_creation_kwargs['system'] = system_prompt
        if tools:
            anthropic_message_creation_kwargs['tools'] = tools
            if tool_choice:
                anthropic_message_creation_kwargs['tool_choice'] = tool_choice

        try:
            response_message = self.client.messages.create(**anthropic_message_creation_kwargs)
        except Exception as e:
            print("Unable to generate Anthropic response")
            print(f"Exception: {e}")
            return e, None

        return response_message

    # def old_query(self, message_content, model, context=None, tools=None, tool_choice=None):
    #     if not context:
    #         context = []
    #     message = {
    #         'role': 'user',
    #         'content': message_content
    #     }
    #     context.append(message)
    #
    #     try:
    #         completion = self.client.chat.completions.create(
    #             model=model,
    #             temperature=0,
    #             messages=context,
    #             tools=tools,
    #             tool_choice=tool_choice
    #         )
    #         print("Completion: \n", completion)
    #         tool_calls = completion.choices[0].message.tool_calls
    #         response_content = completion.choices[0].message.content
    #         if response_content:
    #             response_message = {'role': completion.choices[0].message.role, 'content': response_content}
    #             context.append(response_message)
    #         return response_content, tool_calls, context
    #     except Exception as e:
    #         print("Unable to generate OpenAI response")
    #         print(f"Exception: {e}")
    #         return e, None, context
