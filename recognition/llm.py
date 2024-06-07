import asyncio
from openai import AsyncOpenAI
import ast
import numpy as np

class PromptType:
    """
    Enumeration associating an index to each prompt type.
    """
    ARM = 0
    LEG = 1
    HEAD = 2
    count = 3 # number of different prompts
    allTypes = (ARM, LEG, HEAD) # for looping over prompt types

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

angle_base_promt = """You are a penguin character.  You move your body by giving
arrays of angles, in the Python format.  You willgive tables of angles for doing
a specific action given by the user.  The table should have at least 20 entries,
each representing a different frame of the animation. Remember to always end on
the neutral position.  Do not write comments and return only the array.  For
now, you will only have to move a specific part of your body, do not move this
body part if it is not required.  Here is an exemple of what you should generate
:
"""

arm_example = """
[[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
"""

arm_prompt = """
You are responsible for moving the arms. When in neutral position, the angles
are [0, 0]. The first value is the right arm and the second is the left one.
The arms should make big movements, like raising them completely (which is at a
180-degree angle).
"""

leg_example = arm_example

leg_prompt = """
You are responsible for moving the legs. When in neutral position, the angles
are [0, 0]. The first value is the right leg and the second is the left one.
Leg movements are usually small, try not to exceed 90 degrees.
Do not move if unnecessary for the action.
"""

head_example = """
[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]
"""

head_prompt = """
You are responsible for moving the head. When in neutral position, the angle is
0. Make sure to return to that position after every move. Do not go beyond -90
and 90 degrees. Head movement are usually very small, often between -10 and 10.
Do not move if unnecessary for the action.
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

def interprete_as_nparray(code_as_str):
    """
    Interprete the raw response CODE_AS_STR from the LLM as a Numpy array,
    and return the value if the operation is successful.
    """
    res = None

    try:
        res = np.array(ast.literal_eval(code_as_str))
    except SyntaxError:
        print(f"interprete_as_nparray: invalid syntax '{code_as_str}'")
    except Error as e:
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
