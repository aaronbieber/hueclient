from setuptools import setup

setup(
    name="hueclient",
    version="0.1",
    packages=['hueclient', 'hueclient_script'],
    package_dir={'hueclient': 'src/hueclient',
                 'hueclient_script': 'src/hueclient_script'},
    install_requires=[
        "click",
        "requests>=2.12",
        "colour>=0.1.2"
    ],
    entry_points={
        "console_scripts": [
            "hue-client = hueclient_script.app:main"
        ]
    }
)
