import asyncio
from openai import AsyncOpenAI

class Llm:
    def __init__(self, keyfile, version):
        self.version = version
        key_stream = open(keyfile, 'r')
        key = str(key_stream.readline().strip())

        self.client = AsyncOpenAI(api_key=key)
       
