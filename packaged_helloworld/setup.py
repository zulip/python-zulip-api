import packaged_helloworld
from setuptools import find_packages, setup

package_info = {
    "name": "packaged_helloworld",
    "version": packaged_helloworld.__version__,
    "entry_points": {
        "zulip_bots.registry": ["packaged_helloworld=packaged_helloworld.packaged_helloworld"],
    },
    "packages": find_packages(),
}

setup(**package_info)
