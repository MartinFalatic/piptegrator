#!/usr/bin/env python

import argparse
import sys

from . import common
from . import helper


PARAMS = {}

PARAMS['this_script'] = common.get_script_name_from_filename(__file__)


def setup_and_dispatch():
    parser = argparse.ArgumentParser(
        description=common.format_title(PARAMS['this_script']),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--compile', action='store_true',
                        help='Compile and scrub requirements')
    try:
        args, extra_args = parser.parse_known_args()
    except BaseException as e:
        raise e

    print(common.format_title(PARAMS['this_script']))
    print()

    if sum(map(bool, [args.compile])) > 1:
        common.exit_with_error('Error: Only one top-level option may be specified', parser=parser)
    if args.compile:
        helper.main(scriptname=PARAMS['this_script'], args=extra_args)
    else:
        parser.print_help(sys.stderr)


def main():
    setup_and_dispatch()
    sys.exit(0)


if __name__ == "__main__":
    main()
