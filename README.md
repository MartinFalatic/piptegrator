# Piptegrator

## Tools for managing requirements-driven projects

Run `piptegrator --help` for usage details

Configuration file which contains requirements files (must be in the repo root if present at all):
`.piptegrator_config`

Note: command line options always override corresponding config file options (they do not append to or aggregate with each other).

## Updating this package

Clone this repo

On a branch, make the required edits

Ensure you update the version number in `piptegrator/__config__.py`
(pre-release? use `rc` notation, e.g., `1.2.3rc45`)

### Build and install the distributable wheel

```bash
rm -rf dist build *.egg-info && \
python setup.py bdist_wheel && \
ls -al dist && \
pip uninstall -y piptegrator && \
pip install dist/*.whl
```

### Test the tools

The main tool is `piptegrator`

Given the configuration file `.piptegrator_config` (sample present in this repo)

Run:

```bash
piptegrator --compile --noenvmods --upgrade --help
```

The `--commit` is used to create and manage upgrade branches based on the changed `requirements.txt` files.
This option requires a gitlab token `gitlab_infra_access_token` and optionally the pyup API key `pyup_api_key` in your test environment.

### Test the uploaded artifacts

```bash
pip uninstall -y piptegrator
pip install piptegrator
```
