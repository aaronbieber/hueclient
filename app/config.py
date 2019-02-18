# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser
import os.path
import sys


conf = {}


def load(filename):
    global conf

    if len(conf):
        return conf

    file = os.path.expanduser(filename)
    config = SafeConfigParser()

    if not os.path.exists(file):
        print("Could not read %s." % file)
        print("You may need to run the 'register' command to get set up.")
        sys.exit(1)  # Fatality!
    else:
        config.read(file)
        conf = {
            "ip": config.get("bridge", "ip"),
            "username": config.get("bridge", "username")
        }

    return conf


def save(data, filename):
    file = os.path.expanduser(filename)
    fp = open(file, "w")

    config = SafeConfigParser()
    config.add_section("bridge")
    config.set("bridge", "ip", data["ip"])
    config.set("bridge", "username", data["username"])
    config.write(fp)

    fp.close()
