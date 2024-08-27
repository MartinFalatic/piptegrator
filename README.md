# Piptegrator

## Tools for managing requirements-driven projects

Run `piptegrator --help` for usage details

Configuration file which contains requirements files (must be in the repo root if present at all):
`.piptegrator_config`

Note: command line options always override corresponding config file options (they do not append to or aggregate with each other).

### Running the tools

The main tool is `piptegrator`

```bash
piptegrator --help
```

Given the configuration file `.piptegrator_config` (a sample present in this repo), run:

```bash
piptegrator --compile --noenvmods
```

For use _without_ a config file, specify the requirements input files as a comma delimited string, e.g.:

```bash
piptegrator --compile --noenvmods --requirements test/requirements.in,test/requirements.tests.in
```

### Error resolution

The most common error flagged is when two requirements files have different versions of a given package. You can see an example of this by running

```bash
piptegrator --compile --noenvmods --requirements test-errors/requirements.in,test-errors/requirements.tests.in
```

This kind of mismatch can be trivial (micro version differences) but the purpose of Piptegrator is to flag these:
if you are testing with one version of a library, and deploying with another, unwelcome surprises are possible.

We observe the version mismatches, and can mitigate them by upgrading/downgrading the respective pinned versions accordingly,
or duplicating a troublesome requirement from one requirements file to another.

(The `test` folder has these fixes, and serves as a contrast with the contents of the `test-errors` folder.)

## Updating this package

Clone this repo

On a branch, make the required edits

Ensure you update the version number in `piptegrator/__config__.py`
(pre-release? use `rc` notation, e.g., `1.2.3rc45`)

### Building and install the distributable wheel

```bash
pip install -U build twine && \
rm -rf dist build *.egg-info ; \
python -m build --wheel && \
ls -al dist && \
unzip -l dist/*.whl && \
pip uninstall -y piptegrator && \
pip install dist/*.whl
```

### Quick test (recompiles test/requirements.in with sample options)

```bash
ln -s .piptegrator_config.sample .piptegrator_config  # Or make a copy
piptegrator --compile
```

### Uploading changes (author only)

```bash
twine upload --repository piptegrator dist/*
```
