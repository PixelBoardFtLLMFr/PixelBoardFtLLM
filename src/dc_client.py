import discord
import threading
import asyncio
from discord.ext import tasks

class DCClient:
    def __init__(self, token:str)->None:
        self._token = token
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self.on_ready)
        self._client.event(self.on_message)
        self._message:discord.Message = None
        self._running = False
        self._enabled = False
        self._sending = False
        self._read_thread = None
        self._write_loop = asyncio.new_event_loop()
        pass

    @property 
    def is_running(self):
        return self._running
    
    @property
    def is_sending(self):
        return self._sending

    @property
    def enabled(self):
        return self._enabled
    
    @enabled.setter
    def enabled(self, value):
        self._enabled = value
    
    @property
    def message(self):
        return self._message
    
    @property
    def cleaned_message(self):
        try:
            return self._message.clean_content.replace(self.bot_display_name, "")
        except:
            return None
    
    def clear_message(self):
        self._message = None
    
    def run(self):
        # self._client.run(token=self._token)
        self._read_thread = threading.Thread(target=self._start_bot, daemon=True)
        self._read_thread.start()
        pass

    def _start_bot(self):
        self._client.run(token=self._token)
        pass

    def send_message(self, message:str):
        self._sending = True
        self._client.loop.create_task(self._send_message(message=message))

    def reply_message(self, message:str):
        self._sending = True
        self._client.loop.create_task(self._reply_message(message=message))
        
    async def _send_message(self, message:str):
        await self._message.channel.send(message)

    async def _reply_message(self, message:str):
        await self._message.reply(message)
        self._sending = False
    
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
        print(f'We have logged in as {self._client.user}')

    async def on_message(self, message:discord.Message):
        if not self._enabled or self._sending:
            print("still processing another task")
            return

        if message.author == self._client.user:
            return
        
        if message.content.startswith(self.bot_tag):
            self._message = message