# Body
[![pypi version](https://img.shields.io/pypi/v/body-oc.svg)](https://pypi.org/project/body-oc) ![Custom License](https://img.shields.io/pypi/l/body-oc.svg)

Provides classes to create RESTlike micro-services with minimal configuration.

Please see [LICENSE](https://github.com/ouroboroscoding/body/blob/main/LICENSE)
for further information.

## JavaScript/TypeScript
Check out [@ouroboros/body](https://www.npmjs.com/package/@ouroboros/body)
on npm if you want to easily connect to body services in your choice of
javascript / typescript framework.

## Contents
- [Module Install](#module-install)
- [Module Configuration](#module-configuration)
  - [Example Configuration](#example-configuration)
  - [Configuration Sections](#configuration-sections)
- [Body Docs](#body-docs)
- [Constants](#constants)
- [Error Codes](#error-codes)
- [Regular Expressions](#regular-expressions)
- [Response](#response)
- [REST](#rest)
- [Service](#service)

## Module Install

### Requires
body_oc requires python 3.10 or higher

### Install via pip
```console
foo@bar:~$ pip install body_oc
```

[ [top](#body), [contents](#contents) ]

## Module Configuration
Body services use [JSON](https://www.json.org/) to store their server side
settings. For more information on how to setup and store these configuration
files, visit [config_oc](https://pypi.org/project/config-oc/).

### Example Configuration
Below is a sample configuration file, we'll break it down section by section
immediately after.

```json
{
  "body": {
    "rest": {
      "allowed": [ "mydomain.com" ],
      "default": {
        "domain": "localhost",
        "host": "0.0.0.0",
        "protocol": "http"
      },
      "services": {
        "brain": { "port": 8000, "workers": 10 },
        "mouth": { "port": 8001, "workers": 2 }
      }
    }
  },

  "memory": {
    "redis": "session"
  },

  "redis": {
    "records": {
      "host": "redis.mydomain.com",
      "db": 0
    },
    "session": {
      "host": "redis.mydomain.com",
      "db": 1
    }
  }
}
```

[ [top](#body), [contents](#contents),
[module configuration](#module-configuration) ]

### Configuration Sections
First, we'll start with the lowest level thing we control, the caching software
connection settings. After that we'll talk about other Ouroboros Coding
software, the memory and body settings.

#### redis section
```json
  "redis": {
    "records": {
      "host": "redis.mydomain.com",
      "db": 0
    },
    "session": {
      "host": "redis.mydomain.com",
      "db": 1
    }
  }
```
Each object under the "redis" section represents a named [Redis](https://redis.io/)
connection. The important part is the name, we have two here, **records** and
**session**.

For more info on what can be put under each name, see the extensive
list on [Connecting to Redis](https://redis.readthedocs.io/en/stable/connections.html).

[ [top](#body), [contents](#contents),
[module configuration](#module-configuration),
[configuration sections](#configuration-sections) ]

#### memory section
```json
  "memory": {
    "redis": "session"
  }
```
[memory_oc](https://pypi.org/project/memory_oc/) is an Ouroboros Coding module
that handles the sessions for all services that run on the Body framework.

It needs to know which [Redis](https://redis.io/) connection it should use to
store the session information. We have two from the redis section, **records**
and **session**, and we are telling [memory_oc](https://pypi.org/project/memory_oc/)
to use the **session** one.

[ [top](#body), [contents](#contents),
[module configuration](#module-configuration),
[configuration sections](#configuration-sections) ]

#### body section
```json
  "body": {
    "rest": {
      "allowed": [ "mydomain.com" ],
      "default": {
        "domain": "localhost",
        "host": "0.0.0.0",
        "protocol": "http"
      },
      "services": {
        "brain": { "port": 8000, "workers": 10 },
        "mouth": { "port": 8001, "workers": 2 }
      }
    }
  }
```

[body_oc](https://pypi.org/project/body_oc/) is the rest / service framework
that brain runs on top of. There's a lot of data here, but it's really only
setting up two things.

##### body.rest.allowed
Represents the domains that can make cross origin requests to the RESTlike
interface. This is mandatory if requests are being made from browsers, but in no
way affects direct requests via curl / requests / postman / etc. In this case,
we are allowing any pages across `https://mydomain.com`, this includes
`https://mydomain.com/some/page/`, `https://mydomain.com/other`, and
even `https://admin.mydomain.com/`.

To limit to a specific subdomain, change "allowed" to be more specific
```json
      "allowed": [ "admin.mydomain.com" ]
```
this way `https://admin.mydomain.com/` and `https://bob.admin.mydomain.com/`
work, but not `https://mydomain.com/`.

[ [top](#body), [contents](#contents),
[module configuration](#module-configuration),
[configuration sections](#configuration-sections),
[body section](#body-section) ]

##### body.rest.services
Second, in order to know how to both run and connect to
[body_oc](https://pypi.org/project/body_oc/) services, we need to indicate,
what protocol, domain, and port to use to connect, what interface they will
respond to, and how many instances of each we can spin up.

In this instance we have two services, brain and [mouth](https://pypi.org/project/mouth2-oc/).
Brain is available at `http://localhost:8000` and will be running 10 threads
that will be listening on ip `0.0.0.0`, or internal only traffic. Mouth is
available at `http://localhost:8001` and will be running 2 threads that will
also be listening on ip `0.0.0.0`.

We are relying on the defaults to generate some of the data, and this is a very
simplistic initial launch setup. As we launch more servers and spread the load,
you might have the config on the brain server be something more like this where
[mouth](https://pypi.org/project/mouth2-oc/) is running on another server inside
the network.
```json
      "services": {
        "brain": {
          "domain": "localhost",
          "host": "192.168.0.1",
          "port": 80,
          "protocol": "http",
          "workers": 10
        },
        "mouth": {
          "domain": "mouth.mydomain",
          "port": 80,
          "protocol": "http"
        }
      }
```
...or like this, where it's running outside the network
```json
        "mouth": {
          "domain": "mouth.mydomain.com",
          "port": 443,
          "protocol": "https"
        }
```

[ [top](#body), [contents](#contents),
[module configuration](#module-configuration),
[configuration sections](#configuration-sections),
[body section](#body-section) ]

[ [top](#body), [contents](#contents) ]

## Body Docs
`body` Comes with a script to auto generate documentation from
[Service](#service) instances.

For more information, see the [body-docs](body-docs.md) documentation.

[ [top](#body), [contents](#contents) ]

## Constants
Exports a handful of useful constant values.

Valid trimmed and full UUIDs. Good placeholders if an ID is required, but not
yet generated.

```python
EMPTY_TUUID = '00000000000040008000000000000000'
EMPTY_UUID = '00000000-0000-4000-8000-000000000000'
```

Seconds per hour, day, and week.
```python
SECONDS_HOUR = 3600
SECONDS_DAY = 86400
SECONDS_WEEK = 604800
```

[ [top](#body), [contents](#contents) ]

## Error Codes
Exports errors as unsigned integer constants

Errors related to http/https requests
```python
REST_REQUEST_DATA = 100
REST_CONTENT_TYPE = 101
REST_AUTHORIZATION = 102
REST_LIST_TO_LONG = 103
REST_LIST_INVALID_URI = 104
```

Errors related to the service
```python
SERVICE_ACTION = 200
SERVICE_STATUS = 201
SERVICE_CONTENT_TYPE = 202
SERVICE_UNREACHABLE = 203
SERVICE_NOT_REGISTERED = 204
SERVICE_NO_SUCH_NOUN = 205
SERVICE_TO_BE_USED_LATER = 206
SERVICE_CRASHED = 207
SERVICE_NO_DATA = 208
SERVICE_NO_SESSION = 209
```

An error to indicate insufficient rights
```python
RIGHTS = 1000
```

An error to indicate missing or invalid data passed to a request
```python
DATA_FIELDS = 1001
```

An error to indicate a request has already been made / done
```python
ALREADY_DONE = 1002
```

Errors related to database actions
```python
DB_NO_RECORD = 1100
DB_DUPLICATE = 1101
DB_CREATE_FAILED = 1102
DB_DELETE_FAILED = 1103
DB_UPDATE_FAILED = 1104
DB_KEY_BEING_USED = 1105
DB_ARCHIVED = 1106
DB_REFERENCES = 1107
```

[ [top](#body), [contents](#contents) ]

## Regular Expressions
Exports a couple of useful compiled regular expressions.

`EMAIL_ADDRESS` for validating an e-mail address.
```python
from body.regex import EMAIL_ADDRESS
if not EMAIL_ADDRESS.match('me$mydomain.com'):
  # quit
```

`PHONE_NUMBER_NA` for validating North American phone numbers.
```python
from body.regex import PHONE_NUMBER_NA
if not PHONE_NUMBER_NA.match('1(555-555-1234'):
  # quit
```

[ [top](#body), [contents](#contents) ]

## Response
The class returned from all [Service](#service) requests. It contains 3 parts,
any and all of which can be set.

### Response.data
Contains data related to the request, can be considered a valid response to the
request.

```python
from body import Response


[ [top](#body), [contents](#contents) ]

## REST

[ [top](#body), [contents](#contents) ]

## Service

[ [top](#body), [contents](#contents) ]