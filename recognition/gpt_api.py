from openai import OpenAI
import ast
import numpy as np

key_file = open('key.txt', 'r')
key = str(key_file.readline().strip())

client = OpenAI(api_key=key)

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
    ARM = 1
    LEG = 2
    HEAD = 3

angle_base_promt = """In Python, you will need to generate a table of angles
controlling the motion of a character.  You will write the table for the
character doing a specific action given by the user.  The table should have at
least 20 entries, each representing a different frame of animation. Remember to
always end on the neutral position.  Do not write comments and return only the
array. Here is an exemple of what you should generate :
"""

arm_example = """
[[0, 0], [10, -30], [15, -60], [10, -30], [0, 0]]
"""

arm_prompt = """
When in neutral position, the angles are [0, 0].  Remember, for the right arm,
the first angle in an entry, negative angles make it move away from the body.
The arms should make big movements, like raising them completely (which is at a
180-degree angle).
"""

leg_example = arm_example

leg_prompt = """
When in neutral position, the angles are [0, 0].
"""

head_example = """
[[0], [5], [5], [0], [-5], [0]]
"""

head_prompt = """
When in neutral position, the angle is 0.
"""

def build_prompt(kind):
    if kind == PromptType.ARM:
        return angle_base_promt + arm_example + arm_prompt
    elif kind == PromptType.LEG:
        return angle_base_promt + leg_example + leg_prompt
    elif kind == PromptType.HEAD:
        return angle_base_promt + leg_example + leg_prompt

def get_animation_from_emotion(emotion : str):
    completion = client.chat.completions.create(
        model=MODEL,
        messages= [
            {"role" : "system", "content" : chose_prompt},
            {"role" : "user", "content" : f"The detected emotion is : {emotion}"}
        ]
    ).choices[0].message.content

def ask_gpt(system, user):
    """
    Get a raw string form ChatGPT using SYSTEM and USER as prompt.
    """
    return client.chat.completions.create(
        model=MODEL,
        messages= [
            {"role" : "system", "content" : system},
            {"role" : "user", "content" : user}
        ]
    ).choices[0].message.content

def rank_angle(prompt_type : PromptType, prompt, angles):
    system_prompt = None
    if prompt_type == PromptType.ARM:
        system_prompt = rank_prompt_arms
    elif prompt_type == PromptType.LEG:
        system_prompt = rank_prompt_legs
    elif prompt_type == PromptType.HEAD:
        system_prompt = rank_prompt_head
    response = interprete_gpt(ask_gpt(system_prompt, f"The action is : {prompt}. Choose between :\n 0 : {angles[0]}\n1 : {angles[1]}\n2 : {angles[2]}"))
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

def get_angle_from_prompt(prompt : str):
    """
    PROMPT is the user input, for example 'say hi', not the actual prompt given
    to ChatGPT. The result is a 1x5 array of angles :
    [(right_arm, left_arm, right_leg, left_leg, head)]
    """
    angles = {}
    for kind in (PromptType.ARM, PromptType.LEG, PromptType.HEAD):
        angles[kind] = []
        for i in range(3):
            angles[kind] += [interprete_gpt(ask_gpt(build_prompt(kind, f"The requested motion is : {prompt}")))]
        angles[kind] = angles[kind][rank_angle(kind, prompt, angles[kind])]
    # make them all the same length
    maxlen = max(np.shape(arm_angles)[0],
                 np.shape(leg_angles)[0],
                 np.shape(head_angles)[0])
    arm_angles = array_setlength(arm_angles, maxlen)
    leg_angles = array_setlength(leg_angles, maxlen)
    head_angles = array_setlength(head_angles, maxlen)
    print(arm_angles)
    print(leg_angles)
    print(head_angles)

    return np.concatenate((arm_angles, leg_angles, head_angles), axis=1)
