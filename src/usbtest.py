import os
import time


def run_command():
    os.system('schtasks /create /tn "MyAdminTask" /tr "cmd /c echo Hello from elevated command prompt" /sc onlogon /rl highest')
    os.system('schtasks /run /tn "MyAdminTask"')
    time.sleep(1)
    os.system('schtasks /delete /tn "MyAdminTask" /f')
    pass

def reset_usb():
    run_command()
    print(f"---disabling")
    time.sleep(1)
    run_command()
    print(f"+++enabling")
    time.sleep(1)
    print(f"===ready")

if __name__=="__main__":
    reset_usb()