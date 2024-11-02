import discord
import threading
import asyncio
import os
import time
from discord.ext import tasks
from dotenv import load_dotenv

class ReplyCommand:
    SEND = 0
    REPLY = 1

class DCBot:
    def __init__(self, token:str)->None:
        self._token = token
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self.on_ready)
        self._client.event(self.on_message)
        self._message:discord.Message = None
        self._reply_command:int = ReplyCommand.REPLY
        self._reply_message:str = None
        self._running:bool = False
        self._processing:bool = False
        self._thread = None
        pass

    @property 
    def is_running(self):
        return self._running
    
    @property
    def is_processing(self):
        return self._processing
    
    @property
    def message(self):
        return self._message
    
    @property
    def cleaned_message(self):
        try:
            return self._message.clean_content.replace(self.bot_display_name, "")
        except:
            return None
    
    def run(self):
        self.reset_status()
        self._thread = threading.Thread(target=self._start_bot, daemon=True)
        self._thread.start()
        pass

    def _start_bot(self):
        self._client.run(token=self._token)
        pass

    def set_reply_message(self, message:str, cmd:int):
        self._reply_message = message
        self._reply_command = cmd
    
    @property
    def bot_tag(self):
        return f"<@{self._client.user.id}>"
    
    @property
    def bot_name(self):
        return f"@{self._client.user.name}"

    @property
    def bot_display_name(self):
        return f"@{self._client.user.display_name}"
    
    def mentions(self, client_id)->str:
        return f'<@{client_id}>'

    async def on_ready(self):
        self._enabled = True
        self._running = True

    async def on_message(self, message:discord.Message):
        if self._processing:
            print("still processing another task")
            return

        if message.author == self._client.user:
            return
        
        if message.content.startswith(self.bot_tag):
            self._message = message
            self._reply_message = None
            self._processing = True
            try:
                while self._processing:
                    async with message.channel.typing():
                        await asyncio.sleep(1)
                    self._processing = self._reply_message is None
                if self._reply_command == ReplyCommand.REPLY:
                    await self._message.reply(self._reply_message)
                else:
                    await self._message.channel.send(self._reply_message)
            except Exception as error:
                print(error)
                await asyncio.sleep(2)
            self.reset_status()
    
    def reset_status(self):
        self._message = None
        self._reply_message = None
        self._processing = False

if __name__ == "__main__":
    load_dotenv()
    mybot = DCBot(os.getenv('DISCORD_TOKEN'))
    mybot.run()
    while True:
        time.sleep(1)