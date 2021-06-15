# Piptegrator

## Tools for managing requirements-driven projects

Run `piptegrator --help` for usage details

Configuration file which contains requirements files (must be in the repo root if present at all):
`.piptegrator_config`

Note: command line options always override corresponding config file options (they do not append to or aggregate with each other).

### Running the tools

Prerequisites - works best with pip>=21.0, pip-tools>=5.5.0, and click>=7.0

The main tool is `piptegrator`

Given the configuration file `.piptegrator_config` (sample present in this repo), run:

```bash
piptegrator --compile --noenvmods --upgrade --help
```

For use _without_ a config file, specify the requirements input files as a comma delimited string, e.g.:

```bash
piptegrator --compile --noenvmods --requirements test/requirements.in
```

### Gitlab hooks (only with a config file)

The `--commit` option is used to create and manage upgrade branches based on the changed `requirements.txt` files.
This option requires a gitlab token `gitlab_infra_access_token` and optionally the pyup API key `pyup_api_key` in your test environment.

## Updating this package

Clone this repo

On a branch, make the required edits

Ensure you update the version number in `piptegrator/__config__.py`
(pre-release? use `rc` notation, e.g., `1.2.3rc45`)

### Building and install the distributable wheel

```bash
pip install -U build twine && \
rm -rf dist build *.egg-info && \
python -m build --wheel && \
ls -al dist && \
unzip -l dist/*.whl && \
pip uninstall -y piptegrator && \
pip install dist/*.whl
```

### Uploading changes (author only)

```bash
python -m twine upload dist/* -u <username>
```
