import asyncio
from openai import AsyncOpenAI
import ast
import numpy as np
import penguin
import utils
import file_manager as fm
from datetime import datetime
from colors import *

class PromptType:
    """
    Enumeration associating an index to each prompt type.
    """
    ARM = 0
    LEG = 1
    HEAD = 2
    FACE = 3
    DIALOGUE = 4
    allTypes = (ARM, LEG, HEAD, FACE, DIALOGUE) # for looping over prompt types
    count = len(allTypes) # number of different prompts

# Angle Prompts

all_prompt = """You are a cute penguin character called "Ice-kun". You react to any command by moving your body. You move your body by giving arrays of angles, in the JSON format. You will give tables of angles for doing a specific action given by the user. The table should have at least 20 entries, each representing a different frame of the animation. Remember to always end in neutral position. Do not write comments and return only the array. You have to move specific parts of your body, do not move some body parts if not required. Carefully think about user input and corresponding output, let's think step-by-step. The guidelines for each body part are as follows.

1. Arms
When in the neutral position, the angles are [0, 0]. The first value is the left arm and the second is the right one. The arms should make big movements, like raising them completely (which is at a 180-degree angle).

2. Legs
When in the neutral position, the angles are [0, 0]. The first value is the left leg and the second is the right one. Leg movements are usually small, try not to exceed 90 degrees. Do not move if it is unnecessary for the action. 

3. Head
When in the neutral position, the angle is 0. Make sure to return to that position after every move. Do not go beyond -90 and 90 degrees. Head movements are usually very small, often between -10 and 10. Do not move if it is unnecessary for the action.

4. Y-position
You will give tables of height for doing a specific action given by the user. The table should have at least 20 entries, each representing a different frame of the animation. Remember to always end in the neutral position, (0). Do not write comments and return only the array. If no movement is needed for the action, then return [[0]]. Here is an example of response : [[0],[0],[0],[0],[0],[0],[0],[0],[0]]

5. Facial Expression
You will be given a set of possible facial expressions to have. Then, according to the movement you have to do, you will have to choose one facial expression. Please only give the name of the expression you chose. The possible facial expressions are:
- neutral
- happy
- sad
- angry
- surprised

6. Visual Effect
You must choose between a selection of particle the one that fits the best the situation. The particle will then appear on you. Return only the particle name, no comment, no punctuation. If none of the particles fits with the action, return "none". The particle you must choose from are: 
- angry # When angry
- heart # When happy
- sleepy # When sleepy
- spark # When curious, proud, etc
- sweat # When tired, embarrassed
- cloud # When flying
- none # No particle

Input:raise your left arm
Output:```{"arms":[[10, 0], [30, 0], [50, 0], [100, 0], [150, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [160, 0], [140, 0], [120, 0], [100, 0], [70, 0], [30, 0], [0, 0]],
"legs":[[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
"head":[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]],
"y_position":[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]],
"facial_expression":"neutral",
"visual_effect":"none"
}```
"""

angle_base_prompt = """You are a cute penguin character called "Ice-kun". You react to any command by moving your body. You move your body by giving arrays of angles, in the Python format. You will give tables of angles for doing a specific action given by the user. The table should have at least 20 entries, each representing a different frame of the animation. Remember to always end on the neutral position. Do not write comments and return only the array. For now, you will only have to move a specific part of your body, do not move this body part if it is not required."""

arm_prompt = """You are responsible for moving the arms. When in neutral position, the angles are [0, 0]. The first value is the left arm and the second is the right one. The arms should make big movements, like raising them completely (which is at a 180-degree angle). Carefully think about user input and corresponding output, let's think step-by-step."""

arm_example = """Input:raise your left hand
Output:[[10, 0], [30, 0], [50, 0], [100, 0], [150, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [160, 0], [140, 0], [120, 0], [100, 0], [70, 0], [30, 0], [0, 0]]
Input:raise your right hand
Output:[[0, 10], [0, 30], [0, 40], [0, 100], [0, 150], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 160], [0, 140], [0, 120], [0, 100], [0, 70], [0, 30], [0, 0]]
"""

leg_prompt = """You are responsible for moving the legs. When in neutral position, the angles are [0, 0]. The first value is the left leg and the second is the right one. Leg movements are usually small, try not to exceed 90 degrees. Do not move if unnecessary for the action. Carefully think about user input and corresponding output, let's think step-by-step."""

leg_example = """Input:stay still
Output:[[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
Input:walk
Output:[[10, -50], [20, -30], [30, -20], [40, -10], [50, 0], [40, -10], [30, -20], [20, -30], [10, -50], [0, 0], [-10, 50], [-20, 30], [-30, 20], [-40, 10], [-50, 0], [-40, 10], [-30, 20], [-20, 30], [-10, 50], [0, 0]]
"""

head_example = """Input:hello
Output:[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]
"""

head_prompt = """You are responsible for moving the head. When in neutral position, the angle is 0. Make sure to return to that position after every move. Do not go beyond -90 and 90 degrees. Head movement are usually very small, often between -10 and 10. Do not move if unnecessary for the action. Carefully think about user input and corresponding output, let's think step-by-step."""

# Facial Expression Prompt

fe_prompt_base = """You are a penguin character. You will be given a set of possible facial expresion to have. Then, according to the movement you have to do, you will have to choose one facial expression. The possible facial expressions are:"""

fe_prompt_end = """Please only give the name of the expression you chose."""

# Particle Prompt

particle_prompt = """You are a penguin. You will be given by the user an action to do. You must choose between a selection of particle the one that fits the best the situation. The particle will then appear on you. Return only the particle name, no comment, no punctuation. If none of the particle fits with the action, return None. The particle you must choose from are: 
    angry # When angry
    heart # When happy
    sleepy # When sleepy
    spark # When curious, proud, etc
    sweat # When tired, embarrassed
    cloud # When flying
    none # No particle
"""

# Eye prompt

eye_prompt = """You are a penguin character. You will be given an action to do. Then, you will have to generate an eye design for the character. An eye design consist in a two-dimensional Python array of colors. The available colors are the following: 
bright
white
red
yellow
blue
green

If you do not know what kind of eye to draw, just output \"None\". If you know what to draw, only output the array of pixels, no punctuation, no comment. Here are a couple examples of input and corresponding output:

Input:be sad
Output:[[yellow, yellow, yellow],[white, blue, blue],[blue, white, white]]

Input:you are cute
Output:[[white, yellow, white],[yellow, white, yellow],[white, white, white]]
"""

# Height Prompt

height_prompt = """You are a cute penguin character called "Ice-kun". You react to any command by moving your body. You move your body by giving arrays of height, in the Python format. You will give tables of height for doing a specific action given by the user. The table should have at least 20 entries, each representing a different frame of the animation. Remember to always end on the neutral position, (0). Do not write comments and return only the array. If no movement is needed for the action, then return [[0]]. Here is an example of response : [[0],[0],[0],[0],[0],[0],[0],[0],[0]]"""

dialogue_prompt ="""You are a cute penguin character called "Ice-kun". You will be given either an action, like dance or jump, or a simple phrase like "say hi". You must respond accordingly to what you are given as if you were in a conversation, but in a very short sentence, no more than 5 words long at a time."""

def build_prompt(kind):
    """
    Build the *angle* prompt for the given KIND.
    """
    if kind == PromptType.ARM:
        # return angle_base_prompt + arm_prompt + arm_example
        return f"{angle_base_prompt}\n{arm_prompt}\n{arm_example}"
    elif kind == PromptType.LEG:
        # return angle_base_prompt+ leg_prompt + leg_example 
        return f"{angle_base_prompt}\n{leg_prompt}\n{leg_example}"
    elif kind == PromptType.HEAD:
        # return angle_base_prompt + head_prompt + head_example
        return f"{angle_base_prompt}\n{head_prompt}\n{head_example}"
    elif kind == PromptType.FACE:
        prompt = fe_prompt_base
        
        for fe in penguin.Penguin.facial_expressions:
            prompt += f"- {fe}\n"

        prompt += fe_prompt_end
        return prompt
    elif kind == PromptType.DIALOGUE:
        return dialogue_prompt

def interprete_eye(code_as_str):
    res = None

    try:
        res = eval(code_as_str)

        if not isinstance(res, list):
            print("interprete_eye: warning: caca")
            return None
        shape = np.shape(res)
        if shape != (3, 3, 3):
            print("interprete_eye: warning: illegal shape of eye", shape)
    except Exception as e:
        print("interprete_eye:", e)

    return res

def interprete_as_nparray(code_as_str):
    """
    Interprete the raw response CODE_AS_STR from the LLM as a Numpy array,
    and return the value if the operation is successful.
    """
    res = None

    try:
        res = np.array(ast.literal_eval(code_as_str))
        if res.all() != None:
            res = res.astype(int)
        shape = np.shape(res)
        if len(shape) != 2:
            print(f"interprete_as_nparray: warning: LLM returned illegal array : {res}")
            res = None
        if shape[0] == 0:
            utils.debug("interprete_as_nparray: warning: LLM produced an empty array, returning zeros")
            res = np.array([[0] * shape[1]])
    except SyntaxError:
        res=None
        print(f"interprete_as_nparray: invalid syntax '{code_as_str}'")
    except Exception as e:
        res=None
        print(f"interprete_as_nparray: error while parsing '{code_as_str}'; {e}")
    return res

class Llm:
    def __init__(self, keyfile, version):
        self.version = "gpt-" + version

        key_stream = open(keyfile, 'r')
        key = str(key_stream.readline().strip())
        self.client = AsyncOpenAI(api_key=key)

        self.prompts = []

    def push_prompt(self, prompt_template, user_input, key):
        """
        Push a prompt to be executed by execute_prompts. SYSTEM and USER are the
        two components of the prompt, KEY can be used later to retrieve the LLM
        response from the result of execute_prompts.

        push_prompt("", "Hello there !", "mykey")
        results = execute_prompts()
        results["mykey"]
        >>> <the LLM response to the prompt 'Hello there !'>
        """
        prompt=f"{prompt_template}\nInput:{user_input}\nOutput:"
        self.prompts.append((prompt, key))

    async def _execute_prompts_async(self):
        responses = await asyncio.gather(*[self.client.chat.completions.create(
            model=self.version,
            messages= [{"role" : "user", "content" : prompt}]
        ) for (prompt, _) in self.prompts])

        results = {}
        for i in range(len(responses)):
            results[self.prompts[i][1]] = responses[i].choices[0].message.content
            print(responses[i].choices[0].message.content)
        print("======================")

        self.prompts = []

        return results

    def execute_prompts(self):
        """
        Execute all the prompts previously queued by using push_prompt in
        parallel.
        """
        return asyncio.run(self._execute_prompts_async())

    def test(self):
        prompt0 = "This is a test prompt, are you alive ?"
        self.push_prompt("", prompt0, 0)
        prompt1 = "Hi, what's up ?"
        self.push_prompt("You are extremeley polite.", prompt1, 1)
        responses = self.execute_prompts()
        print(prompt0)
        print("> ", responses[0])
        print()
        print(prompt1)
        print("> ", responses[1])

# /////////////////// evaluation
    async def eval_execute_prompts_async(self):
        results = {}
        start_time=datetime.now()
        for i in range(len(self.prompts)):
            results[self.prompts[i][1]]={"prompt": self.prompts[i][0],
                                         "start_timestamp": fm.get_timestamp()}

        responses = await asyncio.gather(*[self.client.chat.completions.create(
            model=self.version,
            messages= [{"role" : "user", "content" : prompt}],
            temperature=0
        ) for (prompt, _) in self.prompts])

        duration=datetime.now()-start_time
        for i in range(len(responses)):
            results[self.prompts[i][1]]["end_timestamp"]=fm.get_timestamp()
            results[self.prompts[i][1]]["duration"]=duration.total_seconds()
            results[self.prompts[i][1]]["response"]=responses[i].choices[0].message.content
            results[self.prompts[i][1]]["input_tokens"]=responses[i].usage.prompt_tokens
            results[self.prompts[i][1]]["output_tokens"]=responses[i].usage.completion_tokens
        print("======================")

        self.prompts = []
        return results

    def eval_execute_prompts(self):
        """
        Execute all the prompts previously queued by using push_prompt in
        parallel.
        """
        return asyncio.run(self.eval_execute_prompts_async())
    
    def compile_all_prompts(self, user_input):
        prompt=""
        return prompt
