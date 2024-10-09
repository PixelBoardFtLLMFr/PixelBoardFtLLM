import json
import shutil
import pandas as pd
import glob
import os
import traceback
from datetime import datetime

def get_file_name_without_extension(file_path):
    file_name, _ = os.path.splitext(os.path.basename(file_path))
    return file_name

def get_file_extension(file_path):
    _, extension = os.path.splitext(file_path)
    return extension

def get_files_with_extensions(directory, extensions):
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, f'*.{ext}')))
    return files

def write_text(path, content):
    try:
        with open(path, "w", encoding = "utf-8") as f:
            f.write(content)
            f.close()
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')

def read_text(path):
    try:
        with open(path, "r", encoding = "utf-8") as f:
            result = f.read()
            f.close()
            return result
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')
        return ""

def write_json(path, data, compressed=False):
    try:

        if compressed:
            json_object = json.dumps(data)
        else:
            json_object = json.dumps(data, indent = 4)
            
        # Writing to sample.json
        with open(path, "w") as f:
            f.write(json_object)
            f.close()
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')

def read_json(path):
    try:
        with open(path) as f:
            data = json.load(f)
            f.close()
            return data
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')
        return []
    
def write_csv(path, data, header):
    try:
        df = pd.DataFrame(data, columns = header)
        df.to_csv(path, index = False)
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')

def read_csv(path):
    try:
        df = pd.read_csv(path, encoding="utf-8")
        data = df.values.tolist()
        return data
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')
        return []
    
def copy_file(source, destination):
    try:
        shutil.copyfile(source, destination)
    except Exception as e:
        print(f'{str(e)}\n{traceback.format_exc()}')

def get_timestamp():
    return datetime.now().strftime("%Y:%m:%d:%H:%M:%S")