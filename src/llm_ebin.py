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

angle_base_promt = """You are a cute penguin character. You react to any command
by moving your body.  You move your body by giving arrays of angles, in the
Python format.  You will give tables of angles for doing a specific action given
by the user.  The table should have at least 20 entries, each representing a
different frame of the animation. Remember to always end on the neutral
position.  Do not write comments and return only the array.  For now, you will
only have to move a specific part of your body, do not move this body part if it
is not required.
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

# leg_example = """Input:walk
# Output:[[0, 0], [10, 0], [20, 0], [30, 0], [40, 0], [50, 0], [60, 0], [70, 0], [80, 0], [90, 0], [80, 0], [70, 0], [60, 0], [50, 0], [40, 0], [30, 0], [20, 0], [10, 0], [0, 0], [0, 0]]"""

leg_example = """Input:stay still
Output:[[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
Input:walk
Output:[[10, -50], [20, -30], [30, -20], [40, -10], [50, 0], [40, -10], [30, -20], [20, -30], [10, -50], [0, 0], [-10, 50], [-20, 30], [-30, 20], [-40, 10], [-50, 0], [-40, 10], [-30, 20], [-20, 30], [-10, 50], [0, 0]]
"""

head_prompt = """
You are responsible for moving the head. When in neutral position, the angle is
0. Make sure to return to that position after every move. Do not go beyond -90
and 90 degrees. Head movement are usually very small, often between -10 and 10.
Do not move if unnecessary for the action.  Carefully think about user input and
corresponding output, let's think step-by-step.
"""

head_example = """Input:hello
Output:[[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]"""

def build_system_prompt(kind):
    return angle_base_promt

def build_user_prompt(kind, user_input):
    if kind == PromptType.ARM:
        return f"""{arm_prompt}
{arm_example}
Input:{user_input}
Output:"""
    elif kind == PromptType.LEG:
        return f"""{leg_prompt}
{leg_example}
Input:{user_input}
Output:"""
    elif kind == PromptType.HEAD:
        return f"""{head_prompt}
{head_example}
Input:{user_input}
Output:"""

def build_prompt(kind):
    """
    Build the *angle* prompt for the given KIND.
    """
    if kind == PromptType.ARM:
        return angle_base_promt
    elif kind == PromptType.LEG:
        return angle_base_promt
    elif kind == PromptType.HEAD:
        return angle_base_promt
    
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
    except Exception as e:
        print(f"interprete_as_nparray: error while parsing '{code_as_str}'; {e}")

    return res

class LlmEbin:
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
        print("++++response", results)

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
