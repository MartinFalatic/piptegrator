#!/usr/bin/env python

import argparse
import sys

from . import common
from . import helper


PARAMS = {}

PARAMS['this_script'] = common.get_script_name_from_filename(__file__)


def main():
    helper.main(scriptname=PARAMS['this_script'])
    sys.exit(0)


if __name__ == "__main__":
    main()
