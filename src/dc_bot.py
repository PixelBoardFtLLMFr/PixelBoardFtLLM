import discord
import threading
import asyncio
import os
import time
import random
import json
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import datetime
from datetime import time as dtime

class DCBot:
    def __init__(self, token:str, channel_id:int)->None:
        self._token = token
        self._channel_id = channel_id
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)
        self._client.event(self.on_ready)
        self._client.event(self.on_message)
        self._channel = None
        self._thread = None
        self._running:bool = False
        self._active:bool = False
        self._sending:bool = False
        self._animating:bool = False
        self._cached_messages = [] # [message, reply]
        # self._ready_messages = open("ready_commands.txt", 'r').readlines()
        # self._bye_messages = open("bye_commands.txt", 'r').readlines()
        
        self._ready_messages = self.read_txt('ready_commands.txt')
        self._bye_messages = self.read_txt('bye_commands.txt')
        self._instruction_messages = self.read_txt('instruction_commands.txt')
        self._board_enable_token, self._board_disable_token = self._init_important_tokens()
        self._com_token = None
        self._active_times = self._init_active_times()
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
    
    @property
    def communication_token(self):
        return self._com_token
    
    @communication_token.setter
    def communication_token(self, value):
        self._com_token = value

    def set_animating(self, is_animating):
        self._animating = is_animating    
    
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
    
    def _init_important_tokens(self):
        load_dotenv()
        return (os.getenv("BOARD_ENABLE_TOKEN"), os.getenv("BOARD_DISABLE_TOKEN"))
    
    def _str_to_dtime(self, time_str:str)->dtime:
        splitted = time_str.split(':')
        return dtime(hour=int(splitted[0]), minute=int(splitted[1]))
    
    def _get_random_ready_msg(self):
        return " ".join([random.choice(self._ready_messages), self._get_random_instruction_msg()])

    def _get_random_bye_msg(self):
        return random.choice(self._bye_messages).format(t=self._get_next_active_time())
    
    def _get_random_instruction_msg(self):
        return random.choice(self._instruction_messages).format(bot=self.mentions(self._client.user.id))
    
    def _get_next_active_time(self)->str:
        cur_time = datetime.now().time()
        next_time = next((a_t for a_t in self._active_times if cur_time < a_t['min']), None)
        if next_time is None: # we have reach the end of the show
            time_str = self._active_times[0]['min'].strftime("%H:%M")
            return f"tomorrow, at {time_str}"
        else:
            time_str = next_time['min'].strftime("%H:%M")
            print(time_str)
            return f"{time_str}"
        
    def _has_unprocessed_message(self):
        return self.get_unprocessed_message() is not None    
    
    def mentions(self, client_id)->str:
        return f'<@{client_id}>'
    
    def read_txt(self, filepath:str)->list:
        content = None
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.readlines()
            content = [c.strip() for c in content]
            file.close()
        return content
    
    def get_current_active(self)->bool:
        try:
            cur_time = datetime.now().time()
            for act_t in self._active_times:
                if act_t['min'] <= cur_time <= act_t['max']:
                    return True
            pass
        except Exception as error:
            print(f'is_active error:{error}')
            return False

    async def on_ready(self):
        self._running = True
        self._channel = self._client.get_channel(self._channel_id)
        self._client.loop.create_task(self.main_loop())
        print(f'Logged on as {self._client.user} at {self._channel}!')
    
    def get_unprocessed_message(self):
        return next((msg for msg in self._cached_messages if msg[0] is not None and msg[1] is None), None)
        
    def get_cleaned_message(self, message:discord.Message):
        return message.clean_content.replace(self.bot_display_name, "")
    
    def run(self):
        self._thread = threading.Thread(target=self._start_bot, daemon=True)
        self._thread.start()
        pass

    def _start_bot(self):
        self._client.run(token=self._token)
        pass

    def set_reply_message(self, message:str, cmd:int):
        self._reply_message = message
        self._reply_command = cmd
    
    async def set_active(self, active:bool):
        if self._active == active: # no need for update
            return
        
        self._active = active
        if not active:
            self._cached_messages.append([None, self._get_random_bye_msg()])
            self._com_token = self._board_disable_token
            await self._client.change_presence(status = discord.Status.invisible)
        else:
            self._cached_messages.append([None, self._get_random_ready_msg()])
            self._com_token = self._board_enable_token
            await self._client.change_presence(status = discord.Status.online)
        pass

# ==> main loop is here
    async def main_loop(self):
        while True:
            await asyncio.sleep(0.001)

            cur_active = self.get_current_active()
            if self._has_unprocessed_message():
                async with self._channel.typing():
                    await asyncio.sleep(1)
            elif self._active != cur_active:
                await self.set_active(cur_active)
                continue

            s_idx = next((idx for idx, msg in enumerate(self._cached_messages) if msg[1] is not None), -1)
            if s_idx>=0:
                self._sending = True                
                try:
                    s_msg = self._cached_messages.pop(s_idx)
                    if s_msg[0] is not None: # request from user -> reply
                        await self.reply_request(s_msg)
                        self._sending = False
                        await asyncio.sleep(random.uniform(2, 4))
                        while self._animating: # wait until finish animating
                            await asyncio.sleep(0.01)
                        self._cached_messages.append([None, self._get_random_ready_msg()])
                    else:
                        await self.send_message(s_msg)
                except Exception as error:
                    print(error)
                    await asyncio.sleep(2)
                self._sending = False # safe-net
        pass
# ==> main loop is here

    async def reply_request(self, msg_pair:list):
        try:
            d_msg:discord.Message = msg_pair[0]
            print("rep 11")
            async with d_msg.channel.typing():
                await d_msg.reply(msg_pair[1])
            # await d_msg.reply(msg_pair[1])  
            print("rep 22")
        except Exception as error:
            print(error)
            await asyncio.sleep(2)

    async def send_message(self, msg_pair:list):
        try:            
            async with self._channel.typing():
                await self._channel.send(msg_pair[1])
            # await self._channel.send(msg_pair[1])
        except Exception as error:
            print(error)
            await asyncio.sleep(2)

    async def on_message(self, message:discord.Message):
        if message.author == self._client.user:
            return
        
        if self._sending or self._animating or not self._active:
            print("still processing another task")
            return
        
        if message.content.startswith(self.bot_tag):
            self._cached_messages.append([message, None])

if __name__ == "__main__":
    load_dotenv()
    mybot = DCBot(os.getenv('DISCORD_TOKEN'))
    mybot.run()
    while True:
        time.sleep(1)