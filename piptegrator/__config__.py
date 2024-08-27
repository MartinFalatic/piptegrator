
PKGNAME = 'piptegrator'

VERSION = '1.5.0rc2'

DESCRIPTION = 'Piptegrator - Tools for managing requirements-driven projects'

CONFIGFILE = '.piptegrator_config'

CONSOLE_SCRIPTS = {
    'piptegrator': {
        'scriptname': 'piptegrator',
        'path': 'piptegrator',
    },
}

PIP_COMPILE_CMD = ['uv', 'pip', 'compile']
PIP_COMPILE_CMD_LEGACY = ['pip-compile']

PIP_COMPILE_ENV_MODS = {
    'LC_ALL': 'C.UTF-8',
    'LANG': 'C.UTF-8',
}

DEFAULT_SRC_ROOT = '.'
DEFAULT_TGT_ROOT = '.'

DEFAULT_REQUIREMENTS_IN = 'requirements.in'
DEFAULT_INDEX_URL = 'https://pypi.org/simple/'
