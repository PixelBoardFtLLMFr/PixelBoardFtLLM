import discord
import threading
import asyncio
import os
import time
import random
import json
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta
from datetime import time as dtime

class DCPuppetBot:
    def __init__(self, interval:int, token:str, channel_id:int)->None:
        self._token = token
        self._channel_id = channel_id
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self.on_ready)
        self._channel = None
        self._thread = None
        self._running:bool = False
        self._active:bool = False
        self._sending:bool = False

        self._commands = self.read_txt(filepath='./puppet_commands.txt')
        
        self._interval = interval
        self._active_times = self._init_active_times()
        self._reset_time = dtime(hour=1, minute=0)
        pass

    @property 
    def is_running(self)->bool:
        return self._running
    
    @property
    def is_sending(self)->bool:
        return self._sending
    
    @property
    def bot_tag(self):
        return f"<@{self._client.user.id}>"
    
    @property
    def bot_name(self):
        return f"@{self._client.user.name}"

    @property
    def bot_display_name(self):
        return f"@{self._client.user.display_name}"    
    
    def read_txt(self, filepath:str)->list:
        content = None
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.readlines()
            content = [c.strip() for c in content]
            file.close()
        return content
    
    def _init_active_times(self):
        val = []
        with open('active_times.json', 'r') as file:
            j_data = json.load(file)
            for jd in j_data:
                t_pair = {}
                t_pair['min'] = self._str_to_dtime(jd['min'])
                t_pair['max'] = self._str_to_dtime(jd['max'])
                val.append(t_pair)
        return val
        
    def _str_to_dtime(self, time_str:str)->dtime:
        splitted = time_str.split(':')
        return dtime(hour=int(splitted[0]), minute=int(splitted[1]))    
    
    def get_current_active(self)->bool:
        try:
            cur_time = datetime.now().time()
            for act_t in self._active_times:
                if act_t['min'] <= cur_time <= act_t['max']:
                    return True
            return False
        except Exception as error:
            print(f'is_active error:{error}')
            return False

    async def on_ready(self):
        self._running = True
        self._channel = self._client.get_channel(self._channel_id)
        self._client.loop.create_task(self.main_loop())
        print(f'Logged on as {self._client.user} ({self._client.user.id}) at {self._channel}!')
    
    def run(self):
        self._thread = threading.Thread(target=self._start_bot, daemon=True)
        self._thread.start()
        pass

    def mentions(self, client_id)->str:
        return f'<@{client_id}>'

    def _start_bot(self):
        self._client.run(token=self._token)
        pass

# ==> main loop is here
    async def main_loop(self):
        while True:
            await asyncio.sleep(self._interval)
            is_active = self.get_current_active()
            if is_active:
                await self.send_message(message=random.choice(self._commands))
        pass
# ==> main loop is here

    async def send_message(self, message:str):
        try:            
            async with self._channel.typing():
                await self._channel.send(message)
        except Exception as error:
            print(error)
            await asyncio.sleep(2)

if __name__ == "__main__":
    load_dotenv()
    mybot = DCPuppetBot(interval=90, token=os.getenv('DISCORD_PUPPET_TOKEN'), channel_id=int(os.getenv('DISCORD_CHANNEL_ID')))
    mybot.run()
    while True:
        time.sleep(1)