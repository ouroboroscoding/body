# body_oc
[![pypi version](https://img.shields.io/pypi/v/body-oc.svg)](https://pypi.org/project/body-oc)
![Custom License](https://img.shields.io/pypi/l/body-oc.svg)

Provides classes to create RESTlike micro-services with minimal configuration.

Please see [LICENSE](https://github.com/ouroboroscoding/body/blob/main/LICENSE)
for further information.

See [Releases](https://github.com/ouroboroscoding/body/blob/main/releases.md)
for changes from release to release.

See full [documentation](https://github.com/ouroboroscoding/body/blob/main/documentation.md)
for complete description of `body_oc` and how to use it.

## Install

### Requires
rest_mysql requires python 3.10 or higher

### Install via pip
```bash
pip install rest_mysql
```

## Using
When using body as a REST server, you MUST make sure to monkey patch gevent as
the first thing in your code. Nothing else can run before the following:

```python
from gevent import monkey
monkey.patch_all()
```

## JavaScript/TypeScript
Check out [@ouroboros/body](https://www.npmjs.com/package/@ouroboros/body)
on npm if you want to easily connect to body services in your choice of
javascript / typescript framework.

