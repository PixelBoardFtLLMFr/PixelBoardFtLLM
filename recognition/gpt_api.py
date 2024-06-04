from openai import OpenAI, AsyncOpenAI
import ast
import numpy as np
import asyncio

key_file = open('key.txt', 'r')
key = str(key_file.readline().strip())

client = AsyncOpenAI(api_key=key)

MODEL = "gpt-3.5-turbo"
# MODEL = "gpt-4"
#MODEL = "gpt-4-turbo" # more hazardous results
#MODEL = "gpt-4o"

chose_prompt="""
We would like to animate a character according to people's emotions. We have
five different animations:
- idle,
- jump,
- sleepy,
- sad,
- wave.

We also have five particles to add to the animation:
- sweat drop,
- heart,
- spark,
- zzz sleeping,
- angry veins.

I will give you the detected emotion, what animation and what particle
do you advise ? Your response should look like this :

ANIMATION;PARTICLE
"""

rank_prompt_arms = """
In python, a character arms are controlled by an array of angle with (0, 0) being their neutral position.
You will be given 3 arrays and you must choose one that fit the action given by the user the best.
Write only a number between 0 and 2 representing the index of the chosen array, no punctuation, no comment.
"""

rank_prompt_legs = """
In python, a character legs are controlled by an array of angle with (0, 0) being their neutral position.
You will be given 3 arrays and you must choose one that fit the action given by the user the best.
Write only a number between 0 and 2 representing the index of the chosen array, no punctuation, no comment.
"""

rank_prompt_head = """
In python, a character head are controlled by an array of angle with 0 being its neutral position.
You will be given 3 arrays and you must choose one that fit the action given by the user the best.
Write only a number between 0 and 2 representing the index of the chosen array, no punctuation, no comment.
"""

# Sort of enum
class PromptType:
    ARM = 0
    LEG = 1
    HEAD = 2
    count = 3
    allTypes = (ARM, LEG, HEAD)

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
[[0, 0], [10, -30], [15, -30], [10, -30], [0, 0], [0, 0], [0, 0], [0, 0]]
"""

arm_prompt = """
You will only move your arms. When in neutral position, the angles are [0, 0].
The first angle corresponds to your left arm, and the second angle corresponds
to your left arm.  The arms should make big movements, like raising them
completely (which is at a 180-degree angle).
"""

leg_example = arm_example

leg_prompt = """
You are responsible for moving the legs. When in neutral position, the angles
are [0, 0].  Leg movements are usually small, try not to exceed 90 degrees.
"""

head_example = """
[[0], [5], [5], [0], [0], [0], [0], [0], [0], [0], [0], [-5], [0], [0], [0]]
"""

head_prompt = """
You are responsible for moving the head .When in neutral position, the angle is
0.  Make sure to return to that position after every move.  Do not go beyond -90
and 90 degrees.
"""

def build_prompt(kind):
    if kind == PromptType.ARM:
        return angle_base_promt + arm_example + arm_prompt
    elif kind == PromptType.LEG:
        return angle_base_promt + leg_example + leg_prompt
    elif kind == PromptType.HEAD:
        return angle_base_promt + head_example + head_prompt

def get_animation_from_emotion(emotion : str):
    completion = client.chat.completions.create(
        model=MODEL,
        messages= [
            {"role" : "system", "content" : chose_prompt},
            {"role" : "user", "content" : f"The detected emotion is : {emotion}"}
        ]
    ).choices[0].message.content

async def ask_gpt(system, user):
    """
    Get a raw string form ChatGPT using SYSTEM and USER as prompt.
    """
    response = await client.chat.completions.create(
        model=MODEL,
        messages= [
            {"role" : "system", "content" : system},
            {"role" : "user", "content" : user}
        ]
    )

    return response.choices[0].message.content

async def rank_angle(prompt_type : PromptType, prompt, angles):
    system_prompt = None

    if prompt_type == PromptType.ARM:
        system_prompt = rank_prompt_arms
    elif prompt_type == PromptType.LEG:
        system_prompt = rank_prompt_legs
    elif prompt_type == PromptType.HEAD:
        system_prompt = rank_prompt_head

    response = int(interprete_gpt(await ask_gpt(system_prompt, f"The action is : {prompt}. Choose between :\n 0 : {angles[0]}\n1 : {angles[1]}\n2 : {angles[2]}")))

    if isinstance(response, int) and response >= 0 and response < 3:
        return response

    print("Could not interprete GPT response : ", response)
    return 0

def interprete_gpt(code_as_str):
    """
    Interprete the raw response CODE_AS_STR from ChatGPT, and return the value
    if the operations is successful.
    """
    res = None

    try:
        res = np.array(ast.literal_eval(code_as_str))
    except:
        print(f"ChatGPT returned an invalid syntax : {code_as_str}")

    return res

def array_setlength(array, newlen):
    """
    Set numpy array ARRAY to length NEWLEN, either by truncating it if it is too
    long, or by repeating the last element if it is too short.
    """
    currlen = np.shape(array)[0]
    if currlen >= newlen:
        return np.resize(array, (newlen, np.shape(array)[1]))
    else:
        res = np.copy(array)
        for i in range(newlen - currlen):
            res = np.append(res, np.array([array[currlen-1]]), axis=0)
        return res

async def get_angle_from_prompt_async(prompt : str):
    """
    PROMPT is the user input, for example 'say hi', not the actual prompt given
    to ChatGPT. The result is a 1x5 array of angles :
    [(right_arm, left_arm, right_leg, left_leg, head)]
    """
    prompt_count = 3
    angles_tasks = [None]*(prompt_count*PromptType.count)

    for kind in PromptType.allTypes:
        for i in range(prompt_count):
            angles_tasks[kind*3 + i] = ask_gpt(build_prompt(kind), f"The requested motion is : {prompt}")

    angles = await asyncio.gather(*angles_tasks)

    for kind in PromptType.allTypes:
        for i in range(prompt_count):
            angles[kind*3 + i] = interprete_gpt(angles[kind*3 + i])

    rank_tasks = [None]*PromptType.count

    for kind in PromptType.allTypes:
            rank_tasks[kind] = rank_angle(kind, prompt, angles[kind])

    ranks = await asyncio.gather(*rank_tasks)

    bests = [None]*PromptType.count
    for i in PromptType.allTypes:
        bests[i] = angles[i*3 + ranks[i]]

    return bests

def get_angle_from_prompt(prompt: str):
    # make them all the same length
    angles = asyncio.run(get_angle_from_prompt_async(prompt))
    # print("=== ANGLES ===")
    # print(angles)
    maxlen = max(np.shape(angles[PromptType.ARM])[0],
                 np.shape(angles[PromptType.LEG])[0],
                 np.shape(angles[PromptType.HEAD])[0])

    angles[PromptType.ARM] = array_setlength(angles[PromptType.ARM], maxlen)
    angles[PromptType.LEG] = array_setlength(angles[PromptType.LEG], maxlen)
    angles[PromptType.HEAD] = array_setlength(angles[PromptType.HEAD], maxlen)

    # print(angles[PromptType.ARM])
    # print(angles[PromptType.LEG])
    # print(angles[PromptType.HEAD])

    return np.concatenate((angles[PromptType.ARM], angles[PromptType.LEG], angles[PromptType.HEAD]), axis=1)
