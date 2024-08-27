import argparse
import os
import shutil
import subprocess
import sys

from collections import OrderedDict

from . import __config__ as config
from . import common


PARAMS = {}


def parse_file(root_dir, basename, extension, requirements, metadata):
    filename = '{}.{}'.format(os.path.join(root_dir, basename), extension)
    print('-- Parsing', filename)
    rc = 0
    requirements[basename] = []
    lines = []
    reqs_seen_in_this_file = set()
    with open(filename, 'r') as fhandle:
        lines = fhandle.readlines()
    for linenum, line in enumerate(lines):
        parsed_line = common.parse_requirement_file_line(line)
        parsed_line.update({
            'linenum': linenum,
            'filename': filename,
        })
        requirements[basename].append(parsed_line)
        if 'reqname' in parsed_line:
            reqname = parsed_line['reqname']
            if reqname in reqs_seen_in_this_file:
                print('ERROR: req {} already seen in this file'.format(reqname))
                rc = 1
            reqs_seen_in_this_file.add(reqname)
            if reqname not in metadata:
                metadata[reqname] = OrderedDict()
                metadata[reqname]['variant'] = []
                metadata[reqname]['version'] = []
                metadata[reqname]['comment'] = []
                metadata[reqname]['linenum'] = []
                metadata[reqname]['filename'] = []
            metadata[reqname]['variant'].append(parsed_line['variant'])
            metadata[reqname]['version'].append(parsed_line['version'])
            metadata[reqname]['comment'].append(parsed_line['comment'])
            metadata[reqname]['linenum'].append(parsed_line['linenum'])
            metadata[reqname]['filename'].append(parsed_line['filename'])
    return rc


def merge_and_check_metadata(metadata):
    print('-- Merge and validate metadata')
    rc = 0
    for reqname in sorted(metadata):
        req = metadata[reqname]
        filenames = req['filename']
        indices_in_files = [i for i, name in enumerate(filenames) if name.endswith('.in')]
        indices_out_files = [i for i, name in enumerate(filenames) if name.endswith('.txt')]
        variants = req['variant']
        versions = req['version']
        comments = req['comment']
        out_variants = list(OrderedDict.fromkeys([x for i, x in enumerate(variants) if i in indices_out_files]))
        out_versions = list(OrderedDict.fromkeys([x for i, x in enumerate(versions) if i in indices_out_files]))
        in_comments = list(OrderedDict.fromkeys([x for i, x in enumerate(comments) if x != '' and i in indices_in_files]))
        detected_errors = len(out_versions) > 1
        detected_warnings = len(out_variants) > 1
        if detected_errors:
            rc = 1
        if detected_errors or detected_warnings:
            print('{} {:26s} (cver={}, cvar={}) {:52s} {:16s} {:32s} {:48s}'.format(
                'ERROR:  ' if detected_errors else 'WARNING:',
                reqname,
                len(out_versions),
                len(out_variants),
                repr(filenames),
                repr(variants),
                repr(versions),
                repr(comments),
            ))
            print(out_variants, out_versions)
        req['trimmed_input_comments'] = in_comments
    return rc


def regen_file(pip_compile_cmd, root_dir, basename, extension, requirements, metadata):
    filename = '{}.{}'.format(os.path.join(root_dir, basename), extension)
    print('-- Regenerating', filename)
    with open(filename, 'w') as fhandle:
        for req in requirements[basename]:
            if 'other' in req:
                line = req['other']
                if line.startswith('#    {} '.format(' '.join(pip_compile_cmd))):
                    line = '#    {}  # --help for options'.format(PARAMS['this_script'])
            else:
                reqname = req['reqname']
                mdata = metadata[reqname]
                variant = req['variant']
                variant_mod = '[{}]'.format(variant) if variant else ''
                version = req['version']
                comment = req['comment']
                if comment:
                    comments = '  '.join([comment] + mdata['trimmed_input_comments'])
                else:
                    comments = '  '.join(mdata['trimmed_input_comments'])
                comments_mod = '  ' + comments if comments else ''
                line = '{}{}{}{}'.format(reqname, variant_mod, version, comments_mod)
            fhandle.write(line + '\n')
    return 0


def setup():
    parser = argparse.ArgumentParser(
        description=common.format_title(PARAMS['this_script']),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--compile', action='store_true',
                        help='Compile and scrub requirements (always required)')
    parser.add_argument('-U', '--upgrade', action='store_true',
                        help='Upgrade requirements')
    parser.add_argument('--requirements', type=str,
                        help='Comma-delimited requirement.in file(s) (overrides config file)')
    parser.add_argument('--index-url', type=str,
                        help='Override configured index-url')
    parser.add_argument('--noenvmods', action='store_true',
                        help='Don\'t modify the pip-compile environment settings')
    parser.add_argument('--teamcity-mode', action='store_true',
                        help='TeamCity mode (alternate output dir)')
    parser.add_argument('--legacy-tools', action='store_true',
                        help='Transitional - use pip-tools instead of uv)')
    try:
        args, extra_args = parser.parse_known_args()
    except BaseException as e:
        raise e

    print(common.format_title(PARAMS['this_script']))

    if not args.compile:
        common.exit_with_error('Error: no options specified', parser=parser)

    if args.upgrade:
        extra_args.append('--upgrade')

    PARAMS['teamcity_mode'] = args.teamcity_mode
    PARAMS['upgrade'] = args.upgrade
    PARAMS['noenvmods'] = args.noenvmods
    PARAMS['legacy_tools'] = args.legacy_tools
    PARAMS['extra_args'] = extra_args

    config_data = common.get_configfile_data()

    PARAMS['pip_compile_env'] = dict(**os.environ)
    if not PARAMS['noenvmods']:
        PARAMS['pip_compile_env'].update(config.PIP_COMPILE_ENV_MODS)

    common.set_param_from_config(PARAMS, config_data, 'default', 'requirements', None, item_type=str)
    if args.requirements:
        PARAMS['requirements'] = args.requirements
    if PARAMS['requirements']:
        PARAMS['requirements'] = [r.strip() for r in PARAMS['requirements'].split(',')]
    else:
        common.exit_with_error('Error: Requirements must be specified on the command line or in the config file', parser=parser)
    if len(PARAMS['requirements']) != len(set(PARAMS['requirements'])):
        common.exit_with_error('Error: Duplicate requirements specified', parser=parser)

    common.set_param_from_config(PARAMS, config_data, 'default', 'index_url', None, item_type=str)
    if args.index_url:
        PARAMS['index_url'] = args.index_url
    if PARAMS['index_url']:
        extra_args.extend(['--index-url', PARAMS['index_url']])

    common.set_param_from_config(PARAMS, config_data, 'default', 'emit_index_url', None, item_type=bool)
    # Will pass through if it's explicitly given on the command line, config file overrides
    if PARAMS['emit_index_url']:
        extra_args.extend(['--emit-index-url'])

    common.set_param_from_config(PARAMS, config_data, 'default', 'no_strip_extras', None, item_type=bool)
    # Will pass through if it's explicitly given on the command line, config file overrides
    if PARAMS['no_strip_extras']:
        extra_args.extend(['--no-strip-extras'])

    common.set_param_from_config(PARAMS, config_data, 'default', 'unsafe_packages', None, item_type=str)
    if PARAMS['unsafe_packages']:
        if PARAMS['legacy_tools']:
            option_name = '--unsafe-package'
        else:
            option_name = '--no-emit-package'
        for unsafe_package in [r.strip() for r in PARAMS['unsafe_packages'].split(',')]:
            extra_args.extend([option_name, unsafe_package])

    PARAMS['src_root'] = config.DEFAULT_SRC_ROOT
    if PARAMS['teamcity_mode']:
        common.set_param_from_config(PARAMS, config_data, 'default', 'teamcity_tgt_root', config.DEFAULT_TGT_ROOT, item_type=str)
        PARAMS['tgt_root'] = PARAMS['teamcity_tgt_root']
    else:
        PARAMS['tgt_root'] = config.DEFAULT_TGT_ROOT

    PARAMS['basenames'] = common.get_basenames(PARAMS['requirements'])

    print('-- Setup summary:')
    print('    Requirement basenames =', PARAMS['basenames'])
    print('    Upgrade =', PARAMS['upgrade'])
    print('    No env mods =', PARAMS['noenvmods'])
    print('    Source root =', PARAMS['src_root'])
    print('    Target root =', PARAMS['tgt_root'])
    print('    TeamCity mode =', PARAMS['teamcity_mode'])
    print('    Legacy Tools =', PARAMS['legacy_tools'])
    print('    Extra args =', PARAMS['extra_args'])
    print()


def main(scriptname):
    PARAMS['this_script'] = scriptname

    setup()

    all_rcs = []
    reqs_in = {}
    reqs_txt = {}
    reqs_meta = {}

    if PARAMS['legacy_tools']:
        pip_compile_cmd = config.PIP_COMPILE_CMD_LEGACY
    else:
        pip_compile_cmd = config.PIP_COMPILE_CMD

    print('-- Consistency check and rewrites begin')
    print()

    for basename in PARAMS['basenames']:
        in_basename = os.path.join(PARAMS['src_root'], basename)
        out_basename = os.path.join(PARAMS['tgt_root'], basename)
        if PARAMS['src_root'] != PARAMS['tgt_root']:
            common.mkdir_p(os.path.dirname(out_basename))  # Always do this
            if os.path.isfile(in_basename + '.txt'):
                print('-- Copying {} -> {}'.format(in_basename + '.txt', out_basename + '.txt'))
                shutil.copy(in_basename + '.txt', out_basename + '.txt')
        subcommand = pip_compile_cmd + ['--output-file', out_basename + '.txt', in_basename + '.in'] + PARAMS['extra_args']
        print('-- Executing', subcommand)
        print()
        rc = subprocess.call(subcommand, env=PARAMS['pip_compile_env'])
        all_rcs.append(rc)
        print()
        rc = parse_file(root_dir=PARAMS['src_root'], basename=basename, extension='in', requirements=reqs_in, metadata=reqs_meta)
        all_rcs.append(rc)
        print()
        rc = parse_file(root_dir=PARAMS['tgt_root'], basename=basename, extension='txt', requirements=reqs_txt, metadata=reqs_meta)
        all_rcs.append(rc)
        print()

    rc = merge_and_check_metadata(metadata=reqs_meta)
    all_rcs.append(rc)
    print()

    for basename in PARAMS['basenames']:
        rc = regen_file(
            pip_compile_cmd=pip_compile_cmd,
            root_dir=PARAMS['tgt_root'],
            basename=basename,
            extension='txt',
            requirements=reqs_txt,
            metadata=reqs_meta,
        )
        all_rcs.append(rc)
        print()

    print('-- Consistency check and rewrites complete')
    print()
    if any(all_rcs):
        print('!! ERRORS were encountered')
        print()
        sys.exit(1)
    else:
        print('-- No errors were encountered')
        print()
        sys.exit(0)
