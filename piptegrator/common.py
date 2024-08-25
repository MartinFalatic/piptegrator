import configparser
import errno
import getpass
import os
import re
import sys

from collections import OrderedDict
from pathlib import Path

from . import __config__ as config


RE_WITH_COMMENT = re.compile(r'^([^#]+)(.*)$')
RE_WITHOUT_COMMENT = re.compile(r'^([^#]+)()$')
RE_GET_VERSION = re.compile(r'^(.*?)\s*(;|~=|<|<=|>|>=|==|===|\!=)(.*)$')
RE_GET_VARIANT = re.compile(r'^(.*)\[(.*)\]$')

RE_DIFF_LINE = re.compile('^([+-])([^-+]+.*)$')


def parse_urls_from_string(string):
    urls = []
    urls.extend(re.findall(r'http[s]?://[^\s]+', string))
    urls.extend(re.findall(r'git://[^\s]+', string))
    return urls


def trim_relative_filename(filename):
    if filename.startswith('./'):
        filename = filename[2:]
    elif filename.startswith('/'):
        filename = filename[1:]
    return filename


def parse_requirement_file_line(line):
    line = line.rstrip()
    m_with = RE_WITH_COMMENT.match(line)
    if m_with and not m_with.group(1).strip():
        # Preserve indentation of comment-only lines!
        pass
    else:
        line = line.lstrip()
    m_with = RE_WITH_COMMENT.match(line)
    m_without = RE_WITHOUT_COMMENT.match(line)
    if (m_with or m_without) and line[0].isalpha():
        m_req_com = m_with if m_with else m_without
        req_part = m_req_com.group(1).strip()
        comment = m_req_com.group(2).strip()
        m_ver = RE_GET_VERSION.match(req_part)
        if m_ver:
            reqname = m_ver.group(1).strip()
            version_op = m_ver.group(2).strip()
            version_val = m_ver.group(3).strip()
            version = version_op + version_val
        else:
            reqname = req_part
            version_op = ''
            version_val = ''
            version = ''
        variant = ''
        m_var = RE_GET_VARIANT.match(reqname)
        if m_var:
            reqname = m_var.group(1).strip()
            variant = m_var.group(2).strip()
        parsed_line = {
            'reqname': reqname,
            'variant': variant,
            'version_op': version_op,
            'version_val': version_val,
            'version': version,
            'comment': comment,
        }
    else:
        parsed_line = {
            'other': line,
        }
    return parsed_line


def get_secure_input(prompt):
    data = getpass.getpass(prompt)
    return data if data else None


def get_script_name_from_filename(filename):
    basename = os.path.splitext(os.path.basename(filename))[0]
    return config.CONSOLE_SCRIPTS[basename]['scriptname']


def format_title(this_script):
    return '{} v{} via {}'.format(this_script, config.VERSION, config.DESCRIPTION)


def get_basenames(requirements):
    return list(OrderedDict.fromkeys([os.path.splitext(r)[0] for r in requirements]))


def get_configfile_data(configfile_name=config.CONFIGFILE, allow_defaults=True):
    config_data = configparser.ConfigParser()
    config_file = Path(configfile_name)
    if config_file.is_file():
        config_data.read(config_file)
    elif allow_defaults:
        print('Warning: config file {} not found, using default parameters'.format(configfile_name))
        config_data['default'] = {
            'requirements': config.DEFAULT_REQUIREMENTS_IN,
            'index_url': config.DEFAULT_INDEX_URL,
        }
    else:
        exit_with_error('Error: config file {} not found, exiting'.format(configfile_name))
    return config_data


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def exit_with_error(error_text, error_code=1, parser=None):
    print(error_text, file=sys.stderr)
    print(file=sys.stderr)
    if parser:
        parser.print_help(sys.stderr)
    sys.exit(error_code)


def set_param_from_config(params, config_data, config_parent, config_item, default_value, item_type=str):
    if item_type == str:
        params[config_item] = config_data.get(config_parent, config_item, fallback=default_value)
    elif item_type == bool:
        params[config_item] = config_data.getboolean(config_parent, config_item, fallback=default_value)
    elif item_type == int:
        params[config_item] = config_data.getint(config_parent, config_item, fallback=default_value)
    elif item_type == float:
        params[config_item] = config_data.getfloat(config_parent, config_item, fallback=default_value)
