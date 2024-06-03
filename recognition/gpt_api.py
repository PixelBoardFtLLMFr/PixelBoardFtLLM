from openai import OpenAI
import ast

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
[(0, 0), (10, -30), (15, -60), (10, -30), (0, 0)]
"""

arm_prompt = """
When in neutral position, the angles are (0, 0).  Remember, for the right arm,
the first angle in an entry, negative angles make it move away from the body.
The arms should make big movements, like raising them completely (which is at a
180-degree angle).
"""

leg_example = arm_example

leg_prompt = """
When in neutral position, the angles are (0, 0).
"""

head_example = """
[0, 5, 5, 0, -5, 0]
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

def interprete_gpt(code_as_str):
    """
    Interprete the raw response CODE_AS_STR from ChatGPT, and return the value
    if the operations is successful.
    """
    res = None

    try:
        res = ast.literal_eval(code_as_str)
    except:
        print(f"ChatGPT returned an invalid syntax : {code_as_str}")

    return res


def array_setlength(array, newlen):
    """
    Set ARRAY to length NEWLEN, either by truncating it if it is too long, or
    by repeating the last element if it is too short.
    """
    currlen = len(array)
    if currlen >= newlen:
        del array[newlen:]
    else:
        for i in range(newlen - currlen):
            array.append(array[currlen-1])

def get_angle_from_prompt(prompt : str):
    """
    PROMPT is the user input, for example 'say hi', not the actual prompt given
    to ChatGPT. The result is a 1x5 array of angles :
    [(right_arm, left_arm, right_leg, left_leg, head)]
    """
    arm_angles_as_str = ask_gpt(build_prompt(PromptType.ARM),
                                f"The requested motion is : {prompt}")
    arm_angles = interprete_gpt(arm_angles_as_str)

    leg_angles = [(0, 0)]*20

    head_angle = [0]*20

    return [(0, 0, 0, 0, 0)]*20
