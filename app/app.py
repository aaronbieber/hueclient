# -*- coding: utf-8 -*-
import re
import sys
from time import sleep
from urllib.parse import urlparse

import click
import requests

import config
import hue
import ssdp


@click.group()
@click.option("--config",
              default="~/.hue-client.ini",
              metavar="FILE",
              help="Configuration file; defaults to ~/.hue-client.ini.")
@click.pass_context
def main(ctx, config):
    ctx.obj = {"conf_file": config}


def context_load_config(ctx):
    """Return config stored in the file indicated in ctx."""

    if "conf_file" in ctx.obj:
        return config.load(ctx.obj["conf_file"])


def print_light_stats(stats):
    name_width = max(len(stats[k]["name"]) for k in stats.keys())

    print(" ".join(val.ljust(w) for val, w in (("ID", 2),
                                               ("NAME", name_width),
                                               ("POWER", 5),
                                               ("BRIGHT.", 7),
                                               ("COLOR", 5))))

    for id in stats:
        light = stats[id]
        state = light["state"]
        on = "on" if state["on"] is True else "off"
        if "colormode" in state:
            if state["colormode"] == "ct":
                color = state["ct"]
            elif state["hue"] > 0:
                color = state["hue"]
            elif state["xy"][0] > 0 or state["xy"][1] > 0:
                color = "%s, %s" % (state["xy"][0],
                                    state["xy"][1])
        else:
            color = "-"

        light_data = ((id, 2),
                      (light["name"], name_width),
                      (on, 5),
                      (state["bri"], 7),
                      (color, 5))
        print(" ".join(str(val).ljust(w) for val, w in light_data))


def do_return(ret):
    if len(ret) == 1:
        light = ret[list(ret)[0]]

        if light[0] is True:
            status = "updated successfully"
        else:
            status = "failed to update"

        print("Light %s %s." % (list(ret)[0], status))

        if light[0] is True:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("LIGHT  RESPONSE")
        for light_id in ret:
            light = ret[light_id]

            if light[0] is True:
                status = "Updated successfully"
            else:
                status = "Failed (%s)" % light[1]

            print("%s%s" % (str(light_id).ljust(7), status))

        if all([el[0] for el in ret.values()]):
            sys.exit(0)
        else:
            sys.exit(1)


@main.command()
def search():
    """Look for Hue bridges and print their IPs."""

    print("Looking for Hue bridges...")
    devices = ssdp.discover("ssdp:all")
    if len(devices):
        print("Found %s possible devices, one moment..." % len(devices))
        bridges = []
        for d in devices:
            desc = requests.get(d.location)
            if "Philips hue bridge" in desc.text:
                bridges.append(d.location)

        if len(bridges):
            print("\nBridges found:")
            for i in range(0, len(bridges)):
                url = urlparse(bridges[i])
                address = url.netloc
                print("%s\t%s" % (i+1, address))


@main.command()
@click.argument("ip")
@click.pass_context
def register(ctx, ip):
    """Register an authorized user on your bridge."""

    conf_file = ctx.obj["conf_file"]

    url = "http://%s/api" % ip
    payload = {"devicetype": "hue-client.py"}
    r = requests.post(url, json=payload)

    if r.status_code != 200:
        print("Could not communicate with %s. Check the IP, or run 'search'.")
        return
    else:
        print("Please press the button on your Hue bridge...")
        sys.stdout.write("Waiting...")
        for i in range(0, 31):
            sys.stdout.write(" %d" % (30-i))
            sys.stdout.flush()
            r = requests.post(url, json=payload)
            json = r.json()

            if r.status_code == 200 and isinstance(json, list):
                if "success" in json[0] and "username" in json[0]["success"]:
                    username = json[0]["success"]["username"]
                    config.save({"ip": ip, "username": username}, conf_file)
                    print(" Bingo!")
                    print("\nRegistered user %s." % username)
                    break
                else:
                    sleep(1)
                    continue


@main.command()
@click.argument("light_spec")
@click.argument("args", nargs=-1, metavar="ACTION")
@click.pass_context
def lights(ctx, light_spec, args):
    """Get status and make changes to lights.

    LIGHT_SPEC is either the ID of a light, or a list of IDs separated
    by commas, or the word 'all'.

    The ACTION can be 'on', 'off', or a number to set the brightness
    value. If no ACTION is given, the status of the specified lights
    will be printed out.

    Here are some on, off, and brightness examples:

    \b
    lights all on
    lights 5 off
    lights 1,2,3 on
    lights 2,4,6 150

    To change the color of a light, use the action 'temp' or 'hex':

    \b
    lights 1 temp 250
    lights 5 hex 33abf0

    Color temperature ranges from 153 to 500. Hex can be any
    six-character hexadecimal color value (do not include the hash
    symbol used in HTML; just letters and numbers, please).
    """

    conf = context_load_config(ctx)
    light_spec = light_spec.lower()
    cmd = light_spec + " " + " ".join(args)
    if not re.match("(all|\d+(,\s*\d+)*)\s+(on|off|\d+|temp\s+\d+|hex\s+[a-zA-Z0-9]+)", cmd):
        ctx = click.get_current_context()
        click.echo(f"Your command \"{cmd}\" had an error.")
        click.echo(ctx.get_help())
        ctx.exit()
        
    hc = hue.Hue(conf["ip"], conf["username"])

    if light_spec == "all":
        light_spec = hc.get_lights().keys()

    elif light_spec.find(",") > -1:
        light_spec = light_spec.split(",")

    else:
        light_spec = [light_spec]

    if not len(args):
        stats = hc.get_light_state(light_spec)
        print_light_stats(stats)

    elif args[0] == "on":
        do_return(hc.set_light_power(light_spec, True))

    elif args[0] == "off":
        do_return(hc.set_light_power(light_spec, False))

    elif args[0] == "temp":
        if len(args) < 2 or args[1] != str(int(args[1])):
            print("The 'temp' action requires a numeric color temperature.")
            sys.exit(1)

        do_return(hc.set_light_temp(light_spec, args[1]))

    elif args[0] == "hex":
        if len(args) < 2 or len(args[1]) < 6:
            print("The 'hex' action requires a hexadecimal color like ab33cc.")
            sys.exit(1)

        do_return(hc.set_light_hex(light_spec, args[1]))

    elif args[0] == str(int(args[0])):
        # If it's a number...
        do_return(hc.set_light_brightness(light_spec, args[0]))


if __name__ == '__main__':
    main()
