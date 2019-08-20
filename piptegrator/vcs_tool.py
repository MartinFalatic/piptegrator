"""

"""

from __future__ import print_function

import argparse
import gitlab
import os
import re
import requests
import sys
from datetime import datetime
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
from . import __config__ as config
from . import common

PARAMS = {}

PARAMS['start_time_utc'] = datetime.utcnow()
PARAMS['start_time_compact'] = PARAMS['start_time_utc'].strftime('%Y%m%d_%H%M%S')
PARAMS['start_time_nice'] = PARAMS['start_time_utc'].strftime('%Y-%m-%d %H:%M:%S')

PYUP_API_KEY_HEADER = 'X-Api-Key'
PYUP_CHANGELOG_API = 'https://pyup.io/api/v1/changelogs/{}/'
PYUP_METADATA_API = 'https://pyup.io/api/v1/package_metadata/{}/'

DELTA_ADDED = '(new)'
DELTA_REMOVED = '(removed)'

ICON_ADDED = ':sunny:'
ICON_CHANGED = ':eight_spoked_asterisk:'
ICON_REMOVED = ':no_entry:'
ICON_INTERNAL = ':small_orange_diamond:'
ICON_EXTERNAL = ':small_blue_diamond:'
ICON_BUFFER = ''

legend = """
____

### Legend:

&nbsp; &nbsp; &nbsp; &nbsp; {} &nbsp; Added/New package

&nbsp; &nbsp; &nbsp; &nbsp; {} &nbsp; Changed package

&nbsp; &nbsp; &nbsp; &nbsp; {} &nbsp; Removed package

&nbsp; &nbsp; &nbsp; &nbsp; {} &nbsp; Internal package

&nbsp; &nbsp; &nbsp; &nbsp; {} &nbsp; External package

""".format(ICON_ADDED, ICON_CHANGED, ICON_REMOVED, ICON_INTERNAL, ICON_EXTERNAL)

ICON = {
    'added': {
        'internal': ' '.join([s for s in [ICON_ADDED, ICON_INTERNAL, ICON_BUFFER] if s]),
        'external': ' '.join([s for s in [ICON_ADDED, ICON_EXTERNAL, ICON_BUFFER] if s]),
    },
    'changed': {
        'internal': ' '.join([s for s in [ICON_CHANGED, ICON_INTERNAL, ICON_BUFFER] if s]),
        'external': ' '.join([s for s in [ICON_CHANGED, ICON_EXTERNAL, ICON_BUFFER] if s]),
    },
    'removed': {
        'internal': ' '.join([s for s in [ICON_REMOVED, ICON_INTERNAL, ICON_BUFFER] if s]),
        'external': ' '.join([s for s in [ICON_REMOVED, ICON_EXTERNAL, ICON_BUFFER] if s]),
    },
}


def pyup_api_call(reqname, endpoint, pyup_api_key):
    r = requests.get(
        endpoint.format(reqname),
        headers={
            PYUP_API_KEY_HEADER: pyup_api_key,
        },
    )
    if r.status_code == 403:
        print('Warning: Invalid Pyup API key, skipping metadata', file=sys.stderr)
        return None
    if r.status_code == 200:
        return r
    return {}


def get_pyup_metadata(reqs):
    if PARAMS['pyup_api_key']:
        print('-- Gathering requirement information from Pyup')
        for reqname in sorted(reqs):
            print('  Processing {}'.format(reqname))
            changelog = pyup_api_call(reqname, PYUP_CHANGELOG_API, PARAMS['pyup_api_key'])
            if changelog is None:  # API key error
                return None
            elif changelog:
                changelog = changelog.json()
            metadata = pyup_api_call(reqname, PYUP_METADATA_API, PARAMS['pyup_api_key'])
            if metadata is None:  # API key error
                return None
            elif metadata:
                metadata = metadata.json()
            reqs[reqname].update({
                'changelog': changelog,
                'metadata': metadata,
            })
            if not metadata and not changelog:
                print('    -- no Pyup data (internal package?)')
            elif 'links' not in metadata:
                print('    -- changelog but no metadata')
            else:
                print('    -- normal data received')
    else:
        print('-- Skipping Pyup information (no key)')


def format_changes(changes):
    from_val = ''
    to_val = ''
    if '-' in changes:
        from_val = changes['-']
    if '+' in changes:
        to_val = changes['+']
    if not from_val:
        from_val = DELTA_ADDED
    if not to_val:
        to_val = DELTA_REMOVED
    delta = {'old': from_val, 'new': to_val}
    return delta


def parse_diff_info(diffs):
    print('-- Parsing diff data')
    reqs = {}
    filenames = []
    for basename in PARAMS['basenames']:
        filenames.append(common.trim_relative_filename(os.path.join(PARAMS['src_root'], basename) + '.txt'))
    # print(diffs)
    for diff in diffs:
        if diff['new_path'] not in filenames:
            continue
        print('  -- Examining changes to {}'.format(diff['new_path']))
        for line in diff['diff'].split('\n'):
            m = re.match(common.RE_DIFF_LINE, line)
            if m:
                change, req_line = m.groups()
                if change == '+' or change == '-':
                    parsed_line = common.parse_requirement_file_line(req_line)
                    parsed_line['change'] = change
                    if 'reqname' in parsed_line:
                        reqname = parsed_line['reqname']
                        if reqname not in reqs:
                            reqs[reqname] = {}
                            reqs[reqname]['parsed_lines'] = []
                            reqs[reqname]['changes'] = {}
                            reqs[reqname]['parsed_urls'] = set()
                        reqs[reqname]['parsed_lines'].append(parsed_line)
                        reqs[reqname]['changes'][change] = parsed_line['version_val']
                        reqs[reqname]['parsed_urls'].update(common.parse_urls_from_string(req_line))
    return reqs


def converge_pyup_and_diff_data(diffs):
    converged = {}
    reqs = parse_diff_info(diffs)
    if get_pyup_metadata(reqs) is None:
        print('-- Converging diff data only')
    else:
        print('-- Converging diff and Pyup data')
    for reqname in sorted(reqs):
        data = {}

        data['delta'] = format_changes(reqs[reqname]['changes'])

        data['links'] = {}
        if reqs[reqname]['metadata']:
            for subdata in reqs[reqname]['metadata']['links']:
                data['links'][subdata[0]] = subdata[1]
        if reqs[reqname]['parsed_urls']:
            data['links']['Link'] = ' '.join(reqs[reqname]['urls'])

        data['is_internal'] = False
        if not reqs[reqname]['metadata'] and not reqs[reqname]['changelog']:
            if 'Link' in data['links']:
                data['notes'] = 'no Pyup data but link(s) specified (internal package?)'
                data['is_internal'] = True
            else:
                data['notes'] = 'no Pyup data and no link(s) specified (external package?)'
                data['is_internal'] = False
        elif 'links' not in reqs[reqname]['metadata']:
            data['notes'] = 'changelog but no metadata'
        else:
            data['notes'] = 'normal data received'

        print('  Converged summary data for {}'.format(reqname))
        print('    Delta: from {} to {}'.format(data['delta']['old'], data['delta']['new']))
        print('    Internal: {}'.format(data['is_internal']))
        print('    Links:')
        if data['links']:
            for link_name in data['links']:
                link_tgt = data['links'][link_name]
                print('      {}: {}'.format(link_name, link_tgt))
        else:
            print('      (none)')
        converged[reqname] = data
    return converged


def get_markdown_description(converged):
    markdown = []
    markdown.append('## Package version changes versus \'{}\' branch'.format(PARAMS['base_branch']))
    markdown.append('')
    for reqname in sorted(converged):
        data = converged[reqname]
        if data['delta']['old'] == data['delta']['new']:
            print('  Skipping {} - version unchanged {} vs {}'.format(reqname, data['delta']['old'], data['delta']['new']))
            continue
        if data['delta']['old'] == DELTA_ADDED:
            state = 'added'
            details = 'is ADDED at **{}**'.format(data['delta']['new'])
        elif data['delta']['new'] == DELTA_REMOVED:
            state = 'removed'
            details = 'is REMOVED at **{}**'.format(data['delta']['old'])
        else:
            state = 'changed'
            details = 'is CHANGED from **{}** to **{}**'.format(data['delta']['old'], data['delta']['new'])
        icon = ICON[state]['internal'] if data['is_internal'] else ICON[state]['external']
        markdown.append('{} **{}** {}'.format(icon, reqname, details))
        if data['is_internal']:
            markdown.append('* **Internal package**')
        if data['links']:
            for link_name in data['links']:
                link_tgt = data['links'][link_name]
                if link_name == 'Changelog' and data['delta']['new'] != DELTA_REMOVED:
                    link_suffix = '#{}'.format(data['delta']['new'])
                else:
                    link_suffix = ''
                markdown.append('* **{}**: {}{}'.format(link_name, link_tgt, link_suffix))
        else:
            markdown.append('* *(No links available)*')
        markdown.append('')
    markdown.append(legend)
    return '\n'.join(markdown)


def create_merge_request():
    print('-- Processing git data for {}'.format(PARAMS['project_namespace_path']))
    gl = gitlab.Gitlab(PARAMS['gitlab_server'], private_token=PARAMS['gitlab_token'])
    project = gl.projects.get(id=quote(PARAMS['project_namespace_path']))
    actions = []
    for basename in PARAMS['basenames']:
        src_req_file = os.path.join(PARAMS['src_root'], basename) + '.txt'
        src_req_file = common.trim_relative_filename(src_req_file)
        tgt_req_file = os.path.join(PARAMS['tgt_root'], basename) + '.txt'
        os.chmod(tgt_req_file, 0o644)
        print('  Adding data for "{}" from "{}"'.format(src_req_file, tgt_req_file))
        with open(tgt_req_file) as fh:
            actions.append(
                {
                    'action': 'update',
                    'file_path': src_req_file,
                    'content': fh.read(),
                },
            )
    if actions:
        print('-- Committing additions/changes to {}'.format(PARAMS['tgt_branch']))
        commit_message = 'Requirements changes available as of {}'.format(PARAMS['start_time_nice'])
        data = {
            'commit_message': commit_message,
            'actions': actions,
            'branch': PARAMS['tgt_branch'],
        }
        project.branches.create({"branch": PARAMS['tgt_branch'], "ref": PARAMS['base_branch']})
        commit = project.commits.create(data)
        converged = converge_pyup_and_diff_data(commit.diff())
        if not converged:
            print('-- No changes detected - removing branch {}'.format(PARAMS['tgt_branch']))
            project.branches.delete(PARAMS['tgt_branch'])
        else:
            print('-- Creating merge request for {}'.format(PARAMS['tgt_branch']))
            mr_title = '{} Requirements changes available as of {}'.format(PARAMS['pr_prefix'], PARAMS['start_time_nice'])
            mr_desc = get_markdown_description(converged)
            project.mergerequests.create({
                'source_branch':
                    PARAMS['tgt_branch'],
                    'target_branch': PARAMS['base_branch'],
                    'title': mr_title,
                    'description': mr_desc,
                    'labels': [PARAMS['label_prs']],
            })
        if PARAMS['close_prs']:
            print('-- Closing old requirements change PRs by removing their branches')
            branches = project.branches.list(all=True)
            for branch in branches:
                if (
                    branch.name != PARAMS['tgt_branch'] and
                    branch.name.startswith(PARAMS['branch_prefix']) and
                    branch.name != PARAMS['branch_prefix'] and
                    branch.name not in common.PROTECTED_BRANCHES
                ):
                    print('    Deleting defunct branch "{}"'.format(branch.name))
                    branch.delete()
    else:
        print('-- No additions/changes to commit')


def setup(args=None):
    parser = argparse.ArgumentParser(
        description=common.format_title(PARAMS['this_script']),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--base-branch', type=str,
                        help='Base branch (overrides config)')
    parser.add_argument('--gitlab-token', type=str,
                        help='Gitlab token')
    parser.add_argument('--pyup-api-key', type=str,
                        help='Pyup API key')
    parser.add_argument('--teamcity-mode', action='store_true',
                        help='TeamCity mode (alternate input dir)')
    args = parser.parse_args(args)

    PARAMS['teamcity_mode'] = args.teamcity_mode

    config_data = common.get_configfile_data()

    # Env vars take precedence over config vars
    PARAMS['gitlab_server'] = os.environ.get('gitlab_server')
    if not PARAMS['gitlab_server']:
        common.set_param_from_config(PARAMS, config_data, 'default', 'gitlab_server', None)
        if not PARAMS['gitlab_server']:
            common.exit_with_error('Error: gitlab_server must be specified in the environment or the config file', parser=parser)

    PARAMS['vcsrooturl'] = os.environ.get('vcsrooturl')
    if not PARAMS['vcsrooturl']:
        common.set_param_from_config(PARAMS, config_data, 'default', 'vcsrooturl', None)
        if not PARAMS['vcsrooturl']:
            common.exit_with_error('Error: vcsrooturl must be specified in the environment or the config file', parser=parser)

    m = re.match(common.RE_VCS_ROOT_PARSE, PARAMS['vcsrooturl'])
    if m:
        PARAMS['project_namespace_path'] = m.group(1)
    else:
        common.exit_with_error('Error: unable to determine project\'s namespace path')

    common.set_param_from_config(PARAMS, config_data, 'default', 'requirements', None, item_type=str)
    if PARAMS['requirements']:
        PARAMS['requirements'] = [r.strip() for r in PARAMS['requirements'].split(',')]
    else:
        common.exit_with_error('Error: Requirements must be specified in the config file', parser=parser)

    common.set_param_from_config(PARAMS, config_data, 'default', 'pr_prefix', config.DEFAULT_PR_PREFIX)
    common.set_param_from_config(PARAMS, config_data, 'default', 'label_prs', config.DEFAULT_PR_LABEL)
    common.set_param_from_config(PARAMS, config_data, 'default', 'close_prs', config.DEFAULT_CLOSE_PRS, item_type=bool)

    # We are particularly careful about the branch prefix
    common.set_param_from_config(PARAMS, config_data, 'default', 'branch_prefix', config.DEFAULT_BRANCH_PREFIX)
    if not PARAMS['branch_prefix'] or ' ' in PARAMS['branch_prefix'] or PARAMS['branch_prefix'][-1] not in common.BRANCH_PREFIX_VALID_ENDINGS:
        common.exit_with_error('Error: branch_prefix invalid (doesn\'t end in one of {}, is reserved, or has spaces'.format(common.BRANCH_PREFIX_VALID_ENDINGS), parser=parser)

    PARAMS['base_branch'] = args.base_branch
    if not PARAMS['base_branch']:
        common.set_param_from_config(PARAMS, config_data, 'default', 'base_branch', config.DEFAULT_BASE_BRANCH)
    PARAMS['tgt_branch'] = '{}{}'.format(PARAMS['branch_prefix'], PARAMS['start_time_compact'])

    PARAMS['src_root'] = config.DEFAULT_SRC_ROOT
    if PARAMS['teamcity_mode']:
        common.set_param_from_config(PARAMS, config_data, 'default', 'teamcity_tgt_root', config.DEFAULT_TGT_ROOT, item_type=str)
        PARAMS['tgt_root'] = PARAMS['teamcity_tgt_root']
    else:
        PARAMS['tgt_root'] = config.DEFAULT_TGT_ROOT

    PARAMS['basenames'] = common.get_basenames(PARAMS['requirements'])

    # Secure variables are either from the command line, in the environment, or (if not Teamcity) entered securely
    PARAMS['gitlab_token'] = args.gitlab_token
    if not PARAMS['gitlab_token']:
        PARAMS['gitlab_token'] = os.environ.get('gitlab_infra_access_token')
    if not PARAMS['gitlab_token']:
        if PARAMS['teamcity_mode']:
            common.exit_with_error('Error: gitlab_infra_access_token not defined in TeamCity context, cannot prompt for input')
        else:
            PARAMS['gitlab_token'] = common.get_secure_input('Specify gitlab_token:')
            if not PARAMS['gitlab_token']:
                common.exit_with_error('Error: gitlab_token not specified, exiting')

    PARAMS['pyup_api_key'] = args.pyup_api_key
    if not PARAMS['pyup_api_key']:
        PARAMS['pyup_api_key'] = os.environ.get('pyup_api_key')
    if not PARAMS['pyup_api_key']:
        if PARAMS['teamcity_mode']:
            print('Warning: pyup_api_key not defined in TeamCity context - Pyup APIs will not be used')
        else:
            PARAMS['pyup_api_key'] = common.get_secure_input('Specify pyup_api_key:')
            if not PARAMS['pyup_api_key']:
                print('Warning: pyup_api_key not specified - Pyup APIs will not be used')

    print('-- Setup summary:')
    print('    Friendly date = {}'.format(PARAMS['start_time_nice']))
    print('    Source root =', PARAMS['src_root'])
    print('    Target root =', PARAMS['tgt_root'])
    print('    TeamCity mode =', PARAMS['teamcity_mode'])
    print('    Req basenames = {}'.format(PARAMS['basenames']))
    print('    Gitlab server = {}'.format(PARAMS['gitlab_server']))
    print('    Gitlab token = {}'.format('**secret**' if PARAMS['gitlab_token'] else '(empty)'))
    print('    Pyup API key = {}'.format('**secret**' if PARAMS['pyup_api_key'] else '(empty)'))
    print('    VCS root URL = {}'.format(PARAMS['vcsrooturl']))
    print('    Project name = {}'.format(PARAMS['project_namespace_path']))
    print('    Branch prefix = {}'.format(PARAMS['branch_prefix']))
    print('    PR prefix = {}'.format(PARAMS['pr_prefix']))
    print('    Label prs = {}'.format(PARAMS['label_prs']))
    print('    Close prs = {}'.format(PARAMS['close_prs']))
    print('    Base branch = {}'.format(PARAMS['base_branch']))
    print('    Target branch = {}'.format(PARAMS['tgt_branch']))
    print()


def main(scriptname, args):
    PARAMS['this_script'] = scriptname

    setup(args)

    create_merge_request()

    print('-- Done')
    print()

    sys.exit(0)
