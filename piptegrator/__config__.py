
PKGNAME = 'piptegrator'

VERSION = '1.2.2'

DESCRIPTION = 'Piptegrator - Tools for managing requirements-driven projects'

CONFIGFILE = '.piptegrator_config'

CONSOLE_SCRIPTS = {
    'piptegrator': {
        'scriptname': 'piptegrator',
        'path': 'piptegrator',
    },
}

PIP_COMPILE_CMD = 'pip-compile'

PIP_COMPILE_ENV_MODS = {
    'LC_ALL': 'C.UTF-8',
    'LANG': 'C.UTF-8',
}

DEFAULT_SRC_ROOT = '.'
DEFAULT_TGT_ROOT = '.'

DEFAULT_BASE_BRANCH = 'develop'
DEFAULT_BRANCH_PREFIX = 'piptegrator/'
DEFAULT_PR_PREFIX = 'PIPTEGRATOR:'
DEFAULT_PR_LABEL = 'piptegrator'
DEFAULT_CLOSE_PRS = False
