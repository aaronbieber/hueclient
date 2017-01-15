from urlparse import urlparse
from time import sleep
import sys
import click
import requests

import ssdp
import config
import hue


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
                if ":" in address:
                    address = address[:address.index(":")]
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
@click.argument("args", nargs=-1)
@click.pass_context
def lights(ctx, light_spec, args):
    """Get status and make changes to lights.

    LIGHT_SPEC is either the ID of a light, or a list of IDs separated
    by commas, or the word 'all'."""

    conf = context_load_config(ctx)
    light_spec = light_spec.lower()

    hc = hue.Hue(conf["ip"], conf["username"])

    if light_spec == "all":
        light_spec = hc.get_lights().keys()

    elif light_spec.find(",") > -1:
        light_spec = light_spec.split(",")

    else:
        light_spec = [light_spec]

    if not len(args):
        stats = hc.get_light_state(light_spec)
        name_width = max(len(stats[k]["name"]) for k in stats.keys())

        print " ".join(val.ljust(w) for val, w in (("ID", 2),
                                                   ("NAME", name_width),
                                                   ("POWER", 5),
                                                   ("BRIGHT.", 7),
                                                   ("COLOR", 5)))

        for id in stats.keys():
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
            print " ".join(str(val).ljust(w) for val, w in light_data)

    elif args[0] == "on":
        hc.set_light_power(light_spec, True)

    elif args[0] == "off":
        hc.set_light_power(light_spec, False)

    elif args[0] == str(int(args[0])):
        # If it's a number...
        hc.set_light_brightness(light_spec, args[0])


if __name__ == '__main__':
    main()
