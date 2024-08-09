from openai import OpenAI
import base64
import requests
import argparse

key_stream = open("./key.txt", 'r')
key=str(key_stream.readline().strip())
client=OpenAI(api_key=key)

system_prompt="""You are a professional animator for 2D graphic that is familiar with sprite sheet animation. You can tell the difference between sprite sheet animations in terms of the motion, visual, and emotion behind the given animations."""
prompt="""What is the similarity of the two sprite sheet animations? Both animations depict the same cute blue penguin character. Evaluate the similarity between the given animations and give your reasoning. Give your answer in 0--1 scale enclosed between "***"."""
# prompt="""What are those images? Is there any diffenrence between them?"""
# prompt="""Can you tell how many images are provided as the input?"""

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_similarity(img_path_1, img_path_2, output_file):
    img_1=encode_image(image_path=img_path_1)
    img_2=encode_image(image_path=img_path_2)

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "system",
        "content": system_prompt
        },
        {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_1}",
            }
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_2}",
            },
            },
        ],
        }
    ]
    )

    content=response.choices[0].message.content
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"==========\n{content}\n==========")

if __name__=="__main__":
    arg_parser = argparse.ArgumentParser(prog="sprite-atlas", description="sprite-atlas")
    arg_parser.add_argument("-p1", "--picture_1", type=str, required=True, help="the first picture")
    arg_parser.add_argument("-p2", "--picture_2", type=str, required=True, help="the second picture")
    arg_parser.add_argument("-t", "--target_file", type=str, required=True, help="target file")
    args = arg_parser.parse_args()
    get_similarity(args.picture_1, args.picture_2, args.target_file)