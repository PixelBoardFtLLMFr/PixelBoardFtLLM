import asyncio
from openai import AsyncOpenAI
import ast
import numpy as np
import penguin
import utils
from colors import *

class PromptType:
    """
    Enumeration associating an index to each prompt type.
    """
    ARM = 0
    LEG = 1
    HEAD = 2
    FACE = 3
    allTypes = (ARM, LEG, HEAD, FACE) # for looping over prompt types
    count = len(allTypes) # number of different prompts

# Ranking Prompts

rank_prompt_arms = """In python, a character arms are controlled by an array of
angle with (0, 0) being their neutral position.  You will be given 3 arrays and
you must choose one that fit the action given by the user the best.  Write only
a number between 0 and 2 representing the index of the chosen array, no
punctuation, no comment.
"""

rank_prompt_legs = """In python, a character legs are controlled by an array of
angle with (0, 0) being their neutral position.  You will be given 3 arrays and
you must choose one that fit the action given by the user the best.  Write only
a number between 0 and 2 representing the index of the chosen array, no
punctuation, no comment.
"""

rank_prompt_head = """In python, a character head are controlled by an array of
angle with 0 being its neutral position.  You will be given 3 arrays and you
must choose one that fit the action given by the user the best.  Write only the
number representing the index of the chosen array, no punctuation, no comment.
"""

# Angle Prompts

angle_base_promt = """You are a cute penguin character called
"Ice-kun". You react to any command by moving your body.  You move
your body by giving arrays of angles, in the Python format.  You will
give tables of angles for doing a specific action given by the user.
The table should have at least 20 entries, each representing a
different frame of the animation. Remember to always end on the
neutral position.  Do not write comments and return only the array.
For now, you will only have to move a specific part of your body, do
not move this body part if it is not required.
"""

arm_prompt = """
You are responsible for moving the arms. When in neutral position, the angles
are [0, 0].  The first value is the left arm and the second is the right one.
The arms should make big movements, like raising them completely (which is at a
180-degree angle).  Carefully think about user input and corresponding output,
let's think step-by-step.
"""

arm_example = """Input:raise your left hand
Output:[[10, 0], [30, 0], [50, 0], [100, 0], [150, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [160, 0], [140, 0], [120, 0], [100, 0], [70, 0], [30, 0], [0, 0]]
Input:raise your right hand
Output:[[0, 10], [0, 30], [0, 40], [0, 100], [0, 150], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 160], [0, 140], [0, 120], [0, 100], [0, 70], [0, 30], [0, 0]]
"""

leg_prompt = """
You are responsible for moving the legs. When in neutral position, the angles
are [0, 0]. The first value is the left leg and the second is the right one.
Leg movements are usually small, try not to exceed 90 degrees.  Do not move if
unnecessary for the action.  Carefully think about user input and corresponding
output, let's think step-by-step.
"""

leg_example = """Input:stay still
Output:[[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
Input:walk
Output:[[10, -50], [20, -30], [30, -20], [40, -10], [50, 0], [40, -10], [30, -20], [20, -30], [10, -50], [0, 0], [-10, 50], [-20, 30], [-30, 20], [-40, 10], [-50, 0], [-40, 10], [-30, 20], [-20, 30], [-10, 50], [0, 0]]
"""

head_example = """Input:hello
Output:[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]"""

head_prompt = """
You are responsible for moving the head. When in neutral position, the angle is
0. Make sure to return to that position after every move. Do not go beyond -90
and 90 degrees. Head movement are usually very small, often between -10 and 10.
Do not move if unnecessary for the action.  Carefully think about user input and
corresponding output, let's think step-by-step.
"""

# Facial Expression Prompt

fe_prompt_base = """You are a penguin character. You will be given a set of possible
facial expresion to have. Then, according to the movement you have to do, you
will have to choose one facial expression. The possible facial expressions are :
"""

fe_prompt_end = """Please only give the name of the expression you chose.
"""

# Particle Prompt

particle_prompt = """You are a penguin. You will be given by the user an action
to do.  You must choose between a selection of particle the one that fits the
best the situation.  The particle will then appear on you. Return only the
particle name, no comment, no punctuation.  If none of the particle fits with
the action, return None.
The particle you must choose from are : 
    angry # When angry
    heart # When happy
    sleepy # When sleepy
    spark # When curious, proud, etc
    sweat # When tired, embarrassed
    cloud # When flying
    question # When you don't know what to do, or cannot do it
    none # No particle
"""

# Eye prompt

eye_prompt = """You are a penguin character. You will be given an action to do.
Then, you will have to generate an eye design for the character. An eye design
consist in a two-dimensional Python array of colors. The available colors are
the following :

bright
white
red
yellow
blue
green

Here are a couple examples of input and corresponding output :

be sad
[[yellow, yellow, yellow],[white, blue, blue],[blue, white, white]]

you are cute
[[white, yellow, white],[yellow, white, yellow],[white, white, white]]

If you do not know what kind of eye to draw, just output \"None\". If you know
what to draw, only output the array of pixels, no punctuation no comment.
"""

def build_prompt(kind):
    """
    Build the *angle* prompt for the given KIND.
    """
    if kind == PromptType.ARM:
        return angle_base_promt + arm_example + arm_prompt
    elif kind == PromptType.LEG:
        return angle_base_promt + leg_example + leg_prompt
    elif kind == PromptType.HEAD:
        return angle_base_promt + head_example + head_prompt
    elif kind == PromptType.FACE:
        prompt = fe_prompt_base
        
        for fe in penguin.Penguin.facial_expressions:
            prompt += f"- {fe}\n"

        prompt += fe_prompt_end
        return prompt

class PromptType:
    """
    Enumeration associating an index to each prompt type.
    """
    ARM = 0
    LEG = 1
    HEAD = 2
    FACE = 3
    allTypes = (ARM, LEG, HEAD, FACE) # for looping over prompt types
    count = len(allTypes) # number of different prompts

# Ranking Prompts

rank_prompt_arms = """In python, a character arms are controlled by an array of
angle with (0, 0) being their neutral position.  You will be given 3 arrays and
you must choose one that fit the action given by the user the best.  Write only
a number between 0 and 2 representing the index of the chosen array, no
punctuation, no comment.
"""

rank_prompt_legs = """In python, a character legs are controlled by an array of
angle with (0, 0) being their neutral position.  You will be given 3 arrays and
you must choose one that fit the action given by the user the best.  Write only
a number between 0 and 2 representing the index of the chosen array, no
punctuation, no comment.
"""

rank_prompt_head = """In python, a character head are controlled by an array of
angle with 0 being its neutral position.  You will be given 3 arrays and you
must choose one that fit the action given by the user the best.  Write only the
number representing the index of the chosen array, no punctuation, no comment.
"""

# Angle Prompts

angle_base_promt = """You are a cute penguin character called
"Ice-kun". You react to any command by moving your body.  You move
your body by giving arrays of angles, in the Python format.  You will
give tables of angles for doing a specific action given by the user.
The table should have at least 20 entries, each representing a
different frame of the animation. Remember to always end on the
neutral position.  Do not write comments and return only the array.
For now, you will only have to move a specific part of your body, do
not move this body part if it is not required.
"""

arm_prompt = """
You are responsible for moving the arms. When in neutral position, the angles
are [0, 0].  The first value is the left arm and the second is the right one.
The arms should make big movements, like raising them completely (which is at a
180-degree angle).  Carefully think about user input and corresponding output,
let's think step-by-step.
"""

arm_example = """Input:raise your left hand
Output:[[10, 0], [30, 0], [50, 0], [100, 0], [150, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [180, 0], [160, 0], [140, 0], [120, 0], [100, 0], [70, 0], [30, 0], [0, 0]]
Input:raise your right hand
Output:[[0, 10], [0, 30], [0, 40], [0, 100], [0, 150], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 180], [0, 160], [0, 140], [0, 120], [0, 100], [0, 70], [0, 30], [0, 0]]
"""

leg_prompt = """
You are responsible for moving the legs. When in neutral position, the angles
are [0, 0]. The first value is the left leg and the second is the right one.
Leg movements are usually small, try not to exceed 90 degrees.  Do not move if
unnecessary for the action.  Carefully think about user input and corresponding
output, let's think step-by-step.
"""

leg_example = """Input:stay still
Output:[[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
Input:walk
Output:[[10, -50], [20, -30], [30, -20], [40, -10], [50, 0], [40, -10], [30, -20], [20, -30], [10, -50], [0, 0], [-10, 50], [-20, 30], [-30, 20], [-40, 10], [-50, 0], [-40, 10], [-30, 20], [-20, 30], [-10, 50], [0, 0]]
"""

head_example = """Input:hello
Output:[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]"""

head_prompt = """
You are responsible for moving the head. When in neutral position, the angle is
0. Make sure to return to that position after every move. Do not go beyond -90
and 90 degrees. Head movement are usually very small, often between -10 and 10.
Do not move if unnecessary for the action.  Carefully think about user input and
corresponding output, let's think step-by-step.
"""

# Facial Expression Prompt

fe_prompt_base = """You are a penguin character. You will be given a set of possible
facial expresion to have. Then, according to the movement you have to do, you
will have to choose one facial expression. The possible facial expressions are :
"""

fe_prompt_end = """Please only give the name of the expression you chose.
"""

# Particle Prompt

particle_prompt = """You are a penguin. You will be given by the user an action
to do.  You must choose between a selection of particle the one that fits the
best the situation.  The particle will then appear on you. Return only the
particle name, no comment, no punctuation.  If none of the particle fits with
the action, return None.
The particle you must choose from are : 
    angry # When angry
    heart # When happy
    sleepy # When sleepy
    spark # When curious, proud, etc
    sweat # When tired, embarrassed
    cloud # When flying
    question # When you don't know what to do, or cannot do it
    none # No particle
"""

# Eye prompt

eye_prompt = """You are a penguin character. You will be given an action to do.
Then, you will have to generate an eye design for the character. An eye design
consist in a two-dimensional Python array of colors. The available colors are
the following :

bright
white
red
yellow
blue
green

Here are a couple examples of input and corresponding output :

be sad
[[yellow, yellow, yellow],[white, blue, blue],[blue, white, white]]

you are cute
[[white, yellow, white],[yellow, white, yellow],[white, white, white]]

If you do not know what kind of eye to draw, just output \"None\". If you know
what to draw, only output the array of pixels, no punctuation, no comment.
"""

def build_prompt(kind):
    """
    Build the *angle* prompt for the given KIND.
    """
    if kind == PromptType.ARM:
        return angle_base_promt + arm_example + arm_prompt
    elif kind == PromptType.LEG:
        return angle_base_promt + leg_example + leg_prompt
    elif kind == PromptType.HEAD:
        return angle_base_promt + head_example + head_prompt
    elif kind == PromptType.FACE:
        prompt = fe_prompt_base
        
        for fe in penguin.Penguin.facial_expressions:
            prompt += f"- {fe}\n"

        prompt += fe_prompt_end
        return prompt

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
        printf("interprete_eye:", e)

    return res

def interprete_as_nparray(code_as_str):
    """
    Interprete the raw response CODE_AS_STR from the LLM as a Numpy array,
    and return the value if the operation is successful.
    """
    res = None

    try:
        res = np.array(ast.literal_eval(code_as_str))
        shape = np.shape(res)
        if len(shape) != 2:
            print(f"interprete_as_nparray: warning: LLM returned illegal array : {res}")
            res = None
        if shape[0] == 0:
            utils.debug("interprete_as_nparray: warning: LLM produced an empty array, returning zeros")
            res = np.array([[0] * shape[1]])
    except SyntaxError:
        print(f"interprete_as_nparray: invalid syntax '{code_as_str}'")
    except Exception as e:
        print(f"interprete_as_nparray: error while parsing '{code_as_str}'; {e}")

    return res

class Llm:
    def __init__(self, keyfile, version):
        self.version = "gpt-" + version

        key_stream = open(keyfile, 'r')
        key = str(key_stream.readline().strip())
        self.client = AsyncOpenAI(api_key=key)

        self.prompts = []

    def push_prompt(self, system, user, key):
        """
        Push a prompt to be executed by execute_prompts. SYSTEM and USER are the
        two components of the prompt, KEY can be used later to retrieve the LLM
        response from the result of execute_prompts.

        push_prompt("", "Hello there !", "mykey")
        results = execute_prompts()
        results["mykey"]
        >>> <the LLM response to the prompt 'Hello there !'>
        """
        self.prompts.append((system, user, key))

    async def _execute_prompts_async(self):
        responses = await asyncio.gather(*[self.client.chat.completions.create(
            model=self.version,
            messages= [
                {"role" : "system", "content" : system},
                {"role" : "user", "content" : user}
            ]
        ) for (system, user, _) in self.prompts])

        results = {}
        for i in range(len(responses)):
            results[self.prompts[i][2]] = responses[i].choices[0].message.content

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
