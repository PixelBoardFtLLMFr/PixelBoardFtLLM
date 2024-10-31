import os
import time

task_id = "MyTask"
# usb_id = "USB\\VID_054C^&PID_05B8\\FB0700322502679D18" # flash drive
usb_id = "USB\\VID_239A^&PID_8121\\DF6254209F54522F" #COM7

# disable_task = f'schtasks /create /tn "{task_id}" /tr "cmd /c devcon /r disable \\"@{usb_id}\\"" /sc onlogon /rl highest'
# enable_task = f'schtasks /create /tn "{task_id}" /tr "cmd /c devcon /r enable \\"@{usb_id}\\"" /sc onlogon /rl highest'

disable_task = f'schtasks /create /tn "{task_id}" /tr "cmd /c devcon disable \\"@{usb_id}\\"" /sc onlogon /rl highest'
enable_task = f'schtasks /create /tn "{task_id}" /tr "cmd /c devcon enable \\"@{usb_id}\\"" /sc onlogon /rl highest'
run_task = f'schtasks /run /tn "{task_id}"'
delete_task = f'schtasks /delete /tn "{task_id}" /f'

def run_command(task:str):
    os.system(task)
    os.system(run_task)
    time.sleep(1)
    os.system(delete_task)
    pass

def reset_usb():
    run_command(task=disable_task)
    print(f"---disabling:{usb_id}")
    time.sleep(5)
    run_command(task=enable_task)
    print(f"+++enabling:{usb_id}")
    time.sleep(5)
    print(f"===ready:{usb_id}")

if __name__=="__main__":
    reset_usb()