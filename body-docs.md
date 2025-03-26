# body-docs
Generates a markdown file of all the requests available per `Service` based on
the python files passed to it.

## Install
`body-docs` comes with [body](./README.md) and doesn't require installation.
However you might get the following message if
[Jinja2](https://jinja.palletsprojects.com/en/stable/) is not installed in your
environment.

```console
foo@bar:~$ body-docs service/rest.py
Using "body-docs" requires that Jinja2 be installed. It is not installed by default to save space on production installs.
To install jinja2 run the following in your venv:

pip install jinja2
```

## Using
`body-docs` works by passing it one or more files that contains classes that
extend `Service`.

It only has one optional argument that works at the moment, `-o [dir]`,
`--output=[dir]`. This is the path to store the markdown files that are created.
One file is created per `Service`.

Assuming 1 (one) `Service` per file, the following

```console
foo@bar:~/my_module$ body-doc -o documentation services/admin.py services/user.py
```

Would produce
```
├── my_module/
│   ├── __init__.py
│   ├── documentation/
│   │   ├── admin.md
│   │   ├── user.md
│   └── services/
│       ├── admin.py
│       ├── user.py
```

### Filename over ride
By default the file name for each `Service` is composed of the class name
converted to all lowercase. `MyService` becomes `myservice`. To change this you
can provide the `docs-file` section in the `Service`'s docblock

```python
class MyService(Service):
	"""My Service

	Does stuff

	docs-file: rest
	"""
```

This would change the file from `myservice.md` to `rest.md`.

## Request Doc Blocks
**coming soon**