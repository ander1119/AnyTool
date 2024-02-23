import json
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
import time
import random
import openai
import os
from arguments import parse_args
from config import *
from openai_utils import call_gpt
args = parse_args()
output_dir = args.output_dir
# import importlib
# module = importlib.import_module(args.openai_config_path.replace('.py',''))
# for name in dir(module):
#     if not name.startswith('_'):
#         globals()[name] = getattr(module, name)
# api_key = globals()['api_key']
# api_version = globals()['api_version']
# model_name = globals()['model_name']
# api_base = globals()['api_base']
if api_type == "azure":
    from openai import AzureOpenAI as Client
else:
    from openai import OpenAI as Client
client = Client(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint = api_base
    )
@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(key, messages, functions=None,function_call=None,key_pos=None, model="gpt-4-32k",stop=None,process_id=0, **args):
    use_messages = []
    for message in messages:
        if not("valid" in message.keys() and message["valid"] == False):
            use_messages.append(message)
    json_data = {
        "model": model_name,
        "messages": use_messages,
        # "seed":123,
        "max_tokens": 1024,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        **args
    }
    if stop is not None:
        json_data.update({"stop": stop})
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    
    try:
        # if model in ["gpt-3.5-turbo-16k-0613","gpt-4-0613", "gpt-4-deployment","gpt-4-32k", 'gpt-4-turbo']:
        #     openai.api_key = key
        # else:
        #     raise NotImplementedError
        # ts = time.time()
        # print(json_data, file=open('output/gpt_io.txt','a'))
        # print(time.time()-ts)
        ts = time.time()
        # json.dump(json_data['messages'], open(os.path.join(output_dir,'messages.json'),'w'), indent=4)
        openai_response = call_gpt(
            **json_data,
        )
        # openai_response = client.chat.completions.create(
        #     **json_data,
        # )
        # print('solve', time.time()-ts, file=open(os.path.join(output_dir,'time.txt'),'a'))
        # json_data = json.loads(str(openai_response))
        json_data = json.loads(openai_response.json())
        json_data["choices"][0]['message'].pop('tool_calls')
        return json_data 

    except Exception as e:
        # print('solve', time.time()-ts, file=open(os.path.join(output_dir,'time.txt'),'a'))
        # # json_data = json.loads(str(openai_response))
        # json_data = json.loads(openai_response.json())
        # json_data["choices"][0]['message'].pop('tool_calls')
        print("Unable to generate ChatCompletion response")
        print(f"OpenAI calling Exception: {e}")
        return e

class ChatGPTFunction:
    def __init__(self, model="gpt-3.5-turbo-16k-0613", openai_key=""):
        self.model = model
        self.conversation_history = []
        self.openai_key = openai_key
        self.time = time.time()
        self.TRY_TIME = 6

    def add_message(self, message):
        self.conversation_history.append(message)

    def change_messages(self,messages):
        self.conversation_history = messages

    def display_conversation(self, detailed=False):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        print("before_print"+"*"*50)
        for message in self.conversation_history:
            print_obj = f"{message['role']}: {message['content']} "
            if "function_call" in message.keys():
                print_obj = print_obj + f"function_call: {message['function_call']}"
            print_obj += ""
            print(
                colored(
                    print_obj,
                    role_to_color[message["role"]],
                )
            )
        print("end_print"+"*"*50)

    def parse(self,functions,process_id,key_pos=None,**args):
        self.time = time.time()
        for conversation in self.conversation_history:
            if 'content' not in conversation:
                conversation['content'] = ''
                print(self.conversation_history, file=open('tmp.txt','a'))
        conversation_history = self.conversation_history
        for _ in range(self.TRY_TIME):
            if _ != 0:
                time.sleep(15)
            if functions != []:
                json_data = chat_completion_request(
                    self.openai_key, conversation_history, functions=functions,process_id=process_id, key_pos=key_pos,**args
                )
            else:
                json_data = chat_completion_request(
                    self.openai_key, conversation_history,process_id=process_id,key_pos=key_pos, **args
                )
            try:
                total_tokens = json_data['usage']['total_tokens']
                message = json_data["choices"][0]["message"]
                if process_id == 0:
                    print(f"[process({process_id})]total tokens: {json_data['usage']['total_tokens']}")

                if "function_call" in message.keys() and "." in message["function_call"]["name"]:
                    message["function_call"]["name"] = message["function_call"]["name"].split(".")[-1]

                return message, 0, total_tokens
            except BaseException as e:
                print(f"[process({process_id})]Parsing Exception: {repr(e)}. Try again.")
                if json_data is not None:
                    print(f"[process({process_id})]OpenAI return: {json_data}")
            

        return {"role": "assistant", "content": str(json_data)}, -1, 0
    
class GPT4Function:
    def __init__(self, model="gpt-4-0613", openai_key=""):
        self.model = model
        self.conversation_history = []
        self.openai_key = openai_key
        self.time = time.time()
        self.TRY_TIME = 6

    def add_message(self, message):
        self.conversation_history.append(message)

    def change_messages(self,messages):
        self.conversation_history = messages

    def display_conversation(self, detailed=False):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        print("before_print"+"*"*50)
        for message in self.conversation_history:
            print_obj = f"{message['role']}: {message['content']} "
            if "function_call" in message.keys():
                print_obj = print_obj + f"function_call: {message['function_call']}"
            print_obj += ""
            print(
                colored(
                    print_obj,
                    role_to_color[message["role"]],
                )
            )
        print("end_print"+"*"*50)

    def parse(self,functions,process_id,key_pos=None,**args):
        self.time = time.time()
        for conversation in self.conversation_history:
            if 'content' not in conversation:
                conversation['content'] = ''
                print(self.conversation_history, file=open('tmp.txt','a'))
        conversation_history = self.conversation_history
        # print(**args)
        for _ in range(self.TRY_TIME):
            if _ != 0:
                time.sleep(15)
            if functions != []:
                json_data = chat_completion_request(
                    self.openai_key, conversation_history, functions=functions,process_id=process_id, key_pos=key_pos,model=self.model, **args
                )
            else:
                json_data = chat_completion_request(
                    self.openai_key, conversation_history,process_id=process_id,key_pos=key_pos, model=self.model, **args
                )
            try:
                total_tokens = json_data['usage']['total_tokens']
                message = json_data["choices"][0]["message"]
                if process_id == 0:
                    print(f"[process({process_id})]total tokens: {json_data['usage']['total_tokens']}")

                if "function_call" in message.keys() and "." in message["function_call"]["name"]:
                    message["function_call"]["name"] = message["function_call"]["name"].split(".")[-1]

                return message, 0, total_tokens
            except BaseException as e:
                print(f"[process({process_id})]Parsing Exception: {repr(e)}. Try again.")
                if json_data is not None:
                    print(f"[process({process_id})]OpenAI return: {json_data}")
            

        return {"role": "assistant", "content": str(json_data)}, -1, 0

if __name__ == "__main__":
    llm = GPT4Function()
    prompt = '''下面这句英文可能有语病，能不能把语病都改掉？
If you think you get the result which can answer the task, call this function to give the final answer. Or, if you think you can't handle the task from this status, call this function to restart. Remember: you should ALWAYS call this function at the end of your try, and the final answer is the ONLY part that will be showed to user, so final answer should contain enough information.
没语病的形式：
'''
    messages = [
        {"role":"system","content":""},
        {"role":"user","content":prompt},
    ]
    llm.change_messages(messages)
    output,error_code,token_usage = llm.parse(functions=[],process_id=0)
    print(output)