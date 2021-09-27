# Prometheus Scrape Config Operator

## Developing

Create and activate a virtualenv with the development requirements:

```sh
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

## Testing

The test setup is based on `tox`.
The following runs linter and unit tests:

```sh
tox
```

If you want to run only the linter, run:

```
tox -e lint
```

Similarly, the unit tests are run with:

```sh
tox -e unit
```
