# Python Hue Client #

This is a very simple Philips Hue client written in Python. It is not
significant that it's written in Python, but to the best of my knowledge the
only other maintained command line Hue client is written in Node. So now there's
one written in Python.

## Installation ##

You should be able to install this using setuptools, assuming that you have
setuptools installed.

`pip install setuptools`

`python setup.py install`

This will install a script called `hue-client` somewhere on your path. You can
now start using `hue-client`!

## Usage ##

This client supports basic operations right now. Adding more operations is not
too difficult, so things will get added as I have time and attention. Pull
requests welcome.

Start by finding your Hue bridge IP. If you know it, great. If you don't,
`hue-client search`.

Now, register a new user on the bridge so that the client is authorized to
control your lights. Run `hue-client register <bridge IP>`, and then press the
button on your Hue bridge. If all goes well, a configuration file will be
written to `~/.hue-client.ini`.

The INI file name and location can be customized by calling `hue-client` with
the option `--config <path to config>`. This is useful for using this client in
a batch processing mode; just copy the config to somewhere the batch script can
find it, and add `--config <path to config>` to the commands it runs.

You can peruse the help yourself with `hue-client --help` and then calling
`--help` on the various sub-commands. Of particular interest is `hue-client
lights --help`.
