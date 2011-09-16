import os
import shutil


def makedirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def remove(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
