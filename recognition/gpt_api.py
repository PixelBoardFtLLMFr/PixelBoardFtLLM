from openai import OpenAI

key_file = open('key.txt', 'r')
key = str(key_file.readline().strip())

client = OpenAI(api_key=key)

MODEL = "gpt-3.5-turbo"
# MODEL = "gpt-4"
#MODEL = "gpt-4-turbo" # more hazardous results
#MODEL = "gpt-4o" # DOES NOT WORK, PERMISSION DENIED

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

angle_promt = """
In Python you will need to generate a table of angles controlling the angles of the arms of a character.
When the arms are by the body, they're at (0, 0) angle.
When the legs are by the body, they're at (0, 0) angle.
When the head of the penguin is straight up, it is at an angle of (0).
An element of the array should then look like this : (angle_left_arm, angle_right_arm, angle_left_leg, angle_right_leg, angle_head)
You will write the table for the character doing a specific action given by the user.
The table should have at least 20 entries, each representing a different frame of animation.
Remember, for the right arm and right leg, negative angles make it move away from the body.
The arms should make big movements, like raising them completely (which is at a 180-degree angle).
Remember to always end on a neutral position (0, 0, 0, 0, 0)
Do not write comments and return only the array. Here is an exemple of the synthax you should generate : 

[ (0, 0, 0, 0, 0), (0, -30, 10, -10, 10), (0, -60, 30, -30, 20), (0, -90, 90, -90, 10), (0, -90, 90, -90, 0), (0, -60, 60, -60, 10), (0, -30, 10, -10, 0), (0, 0, 0 ,0, 0) ]
"""

def get_animation_from_emotion(emotion : str):
    completion = client.chat.completions.create(
        model=MODEL,
        messages= [
            {"role" : "system", "content" : chose_prompt},
            {"role" : "user", "content" : f"The detected emotion is : {emotion}"}
        ]
    )

    return completion.choices[0].message.content

def get_angle_from_prompt(prompt : str):
    completion = client.chat.completions.create(
        model=MODEL,
        messages= [
            {"role" : "system", "content" : angle_promt},
            {"role" : "user", "content" : f"The detected emotion is : {prompt}"}
        ]
    )

    return completion.choices[0].message.content 
