# body_oc
[![pypi version](https://img.shields.io/pypi/v/body-oc.svg)](https://pypi.org/project/body-oc) ![Custom License](https://img.shields.io/pypi/l/body-oc.svg)

Provides classes to create RESTlike micro-services with minimal configuration.

Please see [LICENSE](https://github.com/ouroboroscoding/body/blob/main/LICENSE)
for further information.

See [Releases](https://github.com/ouroboroscoding/body/blob/main/releases.md)
for changes from release to release.

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
- [Calling other Services](#calling-other-services)
- [Constants](#constants)
- [Error Codes](#error-codes)
- [Regular Expressions](#regular-expressions)
- [Response & Error](#response--error)
- [ResponseException](#response-exception)
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

## Calling other Services
In order to call other services Body provides a registration method and a
request method.

### body.register_services
`register_services` is required to be run before any calls to
[request](#bodyrequest). It goes through the `config.body.rest.default` and
`body.rest.services` sections and generates the information necessary to connect
to other services provided by the configuration.

See the [body section](#body-section) for examples of how to setup the config.

When registering your own service, pass a dictionary with its name and the
instance. Multiple services can be passed if you are running them all within
the same process.

```python
from body import register_services, REST
from my_service import MyService

my_service = MyService()

services = register_service({
  'my_service': my_service
})

my_conf = services['my_service']

REST(
  'my_service',
  my_service
).run(
  host = my_conf['host'],
  port = my_conf['port'],
  workers = my_conf['workers']
  timeout = 'timeout' in my_conf \
    and my_conf['timeout'] \
    or 30
)
```

We can see in the above example the added benefit to calling register_services
is it returns a dictionary of the connection settings for each service. This
makes passing those settings to the [REST](#rest) `run()` call a snap without
hardcoding them, or relying on duplicate configuration.

[ [top](#body), [contents](#contents),
[calling other services](#calling-other-services) ]

### body.request
Handles making a request to another service.

```python
import body
body.register_services()
response = body.request(
  'brain', 'create', 'user', { 'data': { 'record':  {} } }
)
```

We are calling the 'create' action on the 'brain' service at the noun 'user',
and passing it data and no session.

`register_services()` must be called before using `request` in order to setup
the networking paths based on the [body](#body-section) section of the
configuration.

[ [top](#body), [contents](#contents),
[calling other services](#calling-other-services) ]

#### body.create
Shortcut for calling [request](#bodyrequest) with the `create` action.
```python
response = body.create(
  'brain', 'user', { 'data': { 'record': { } } }
)
```

[ [top](#body), [contents](#contents),
[calling other services](#calling-other-services) ]

#### body.delete
Shortcut for calling [request](#bodyrequest) with the `delete` action.
```python
response = body.delete(
  'brain', 'user', { 'data': { '_id': 'someid' } }
)
```

[ [top](#body), [contents](#contents),
[calling other services](#calling-other-services) ]

#### body.read
Shortcut for calling [request](#bodyrequest) with the `read` action.
```python
response = body.read(
  'brain', 'user', { 'data': { '_id': 'someid' } }
)
```

[ [top](#body), [contents](#contents),
[calling other services](#calling-other-services) ]

#### body.update
Shortcut for calling [request](#bodyrequest) with the `update` action.
```python
response = body.update(
  'brain', 'user', { 'data': { '_id': 'someid', 'record': { } } }
)
```

[ [top](#body), [contents](#contents),
[calling other services](#calling-other-services) ]

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

## Response & Error
`Response` is the class returned from all [Service](#service) requests. It
contains 3 parts, [data](#responsedata), [error](#responseerror), and
[warning](#responsewarning).

### Response.data
The first argument to the Response constructor is `data` related to the request.
It can be considered a valid response to the request. Here we are returning a
list of records from a READ / GET request.

```python
from body import Response, Service
class MyService(Service):
  def my_request_read(self, req: jobject) -> Response:
    return Response([ """ records """ ])
```

Here we are returning a simple boolean based on a record existing or not
```python
from body import Response, Service
from records.user import User
class MyService(Service):
  def my_request_exists_read(self, req: jobject) -> Response:
    self.check_data(req.data, [ '_id' ])
    return Response(
      User.exists(req.data._id)
    )
```

[ [top](#body), [contents](#contents), [response & error](#response--error) ]

### Response.error
The second argument to Response is `error`, traditionally composed of a `code`
and a `msg`.

Here we are trying to find a user record based on its ID, if the DB can't find
anything, we return only an error with the `code` DB_NO_RECORD, and the `msg`
as a list with the ID that failed and the record type that it failed for.

```python
from body import errors, Response, Service
from records.user import User
class MyService(Service):
  def my_request_read(self, req: jobject) -> Response:
    self.check_data(req.data, [ '_id' ])
    user = User.get(req.data._id)
    if not user:
      return Response(
        error = (
          errors.DB_NO_RECORD,
          [ req.data._id, 'user' ]
        )
      )
    return Response(user)
```

In order to simplify this process, we have the `Error` class which extends
`Response` by simply assuming [data](#responsedata) and [warning](#responsewarning)
are None. Here is the same script as above, but replacing `Response(error=())`
with `Error()`.

```python
from body import Error, errors, Response, Service
from records.user import User
class MyService(Service):
  def my_request_read(self, req: jobject) -> Response:
    self.check_data(req.data, [ '_id' ])
    user = User.get(req.data._id)
    if not user:
      return Error(
        errors.DB_NO_RECORD,
        [ req.data._id, 'user' ]
      )
    return Response(user)
```

[ [top](#body), [contents](#contents), [response & error](#response--error) ]

### Response.warning
The third argument to Response is helpful if the request is successful, but with
caveats. Perhaps that user account was created, but the e-mail notifying the
account creator didn't get sent, an error by itself, but not with the primary
action. Or perhaps you are returning the data requested, but you add a warning
that it, the data, is out of date at the moment.

```python
from body import Response, Service
from records.user import User
from em import send
class MyService(Service):
  def my_request_create(self, req: jobject) -> Response:
    self.check_data(req.data, [ 'record' ])
    _id = User(req.data.record)
    email = send(
      req.data.record.email,
      'Welcome %s!' % req.data.record.first_name,
      { 'html': '<p>Welcome to MyDomain!</p>' }
    )
    return Response(
      _id,
      warning = not email \
        and 'Email notification failed' \
        or None
    )
```

[ [top](#body), [contents](#contents), [response & error](#response--error) ]

# ResponseException
`ResponseException` is useful if you need to call other functions in your
request methods that themselves will generate the `Response` or `Error`.
This is especially helpful for errors.

```python
from body import errors, Response, ResponseException, Service
class MyService(Service):

  @classmethod
  def _my_method(cls, _id):
    raise ResponseException(
      error=(errors.ALREADY_DONE, 'we did it already')
    )

  def my_service_create(self, req: jobject) -> Response:
    self.check_data(req.data, [ '_id' ])
    self._my_method(req.data._id)
    return Response(True)
```

We don't need to check the response to `_my_method` in `my_service_create`
because it will raise a `ResponseException` which will bubble up into
[REST](#rest), or some other interface, and be handled as if it was a normal
`Response` being returned to the client.

## REST
`REST` provides a way to take a service and connect it to the internet via http
requests. It's passed a [Service](#service) instance and looks for the _create,
_read, _update, and _delete methods available and connecting them to POST, GET,
PUT, and DELETE calls, respectively.

```python
from body import REST, Service
import config

class MyService(Service):
  def reset():
    pass
  def my_request_create(self, req: jobject) -> Response:
    return Response(id)
  def my_request_delete(self, req: jobject) -> Response:
    return Response(True)
  def my_request_read(self, req: jobject) -> Response:
    return Response(user)
  def my_request_update(self, req: jobject) -> Response:
    return Response(True)

def errors(error):
  # Available on every request
  for k in [ 'traceback', 'method', 'service', 'path' ]:
    print('%s: %s' % ( k, str(error[k]) ))
  # Request dependant
  for k in [ 'data', 'session', 'environment' ]:
    if k in error:
      print('%s: %s' % ( k, str(error[k]) ))

REST(
  name = 'my_service',
  instance = MyService(),
  cors = config.body.rest.allowed([ 'mydomain.com' ]),
  on_errors = errors,
  verbose = True
).run(
  host = 'localhost',
  port = 80,
  workers = 10,
  timeout = 30
)
```

Here we have created a service, `MyService` with one noun `my/request` that
responds to all 4 methods, meaning all the following would be valid:

`POST my/request`\
`DELETE my/request`\
`GET my/request`\
`PUT my/request`
```python
  name = 'my_service',
  instance = MyService(),
```

It will accept cross origin requests if they come from *.mydomain.com
```python
  cors = config.body.rest.allowed('mydomain.com'),
```

It'll print out any errors if any service requests crash
```python
  on_errors = errors,
```

It'll print out messages about every request it gets and what it returns as a
response.
```python
  verbose = True
```

REST uses [Bottle](https://bottlepy.org/docs/dev/) as the underlying sytem for
adding http functionality. The run command corresponds directly to the
[run()](https://bottlepy.org/docs/dev/api.html) command of Bottle and will
support all the same arguments.

To aid in entering the details for the `run()` method, see
[register_services](#bodyregister_services).

[ [top](#body), [contents](#contents) ]

## Service
`Service` is the class all services should extend. It has one helper method,
one abstract method, and a specific format for any other method which the user
wants to make available to REST, CLI, or some other interface.

### check_data
The `check_data` method is a helper for checking the input to any request
exists before trying to use it.

```python
from body import errors, Response, Service
from records.user import User
from records.permissions import Permissions
class MyService(Service):

  def my_request_create(self, req: jobject) -> Response:

    self.check_data(req.data, [ 'user', 'permissions' ])

    user = User(req.data.user)
    if not user.create():
      return Error(errors.DB_CREATE_FAILED, 'user')

    req.data.permissions.user = user['_id']
    perms = Permissions(req.data.permissions)
    if not permissions.create():
      return Error(errors.DB_CREATE_FAILED, 'permissions')

    return Response(user['_id'])

  def reset():
    pass
```

We don't need to worry about checking the return of `check_data` as it will
raise a [ResponseException](#responseexception) with `error` being a `code` of
[DATA_FIELDS](#error-codes) and a `msg` being a list of keys (fields) to the
string 'missing'. This is consistent with validations errors returned from
[define](https://pypi.org/project/define-oc/) in order to keep a standard for
errors.

For example, if we passed `check_data` the following structure
```python
self.check_date(req.data, [ 'var0', 'var1' ])
```
And we recieved the following in `req.data`
```python
{
  'var1': {
    'sub1': 0,
    'sub2': False
  }
}
```
`check_data` would raise the equivalent of the following `Response`
```python
{
  'error': {
    'code': 1001,
    'msg': [ [ 'var0', 'missing' ] ]
  }
}
```
However, if we passed the following structure indicating we want not just `var0`
and `var1`, but that we must also assure `sub0`, `sub1`, and `sub2` exist within
it
```python
self.check_date(
  req.data,
  [ 'var0', { 'var1': [ 'sub0', 'sub1', 'sub2' ] } ]
)
```
Now the `Response` we get is
```python
{
  'error': {
    'code': 1001,
    'msg': [
      [ 'var0', 'missing' ],
      [ 'var1.sub0', 'missing' ]
    ]
  }
}
```

[ [top](#body), [contents](#contents), [service](#service) ]

### reset
Called when the service(s) are sent a reset request. It's best to do any setup
here, and if required at initialisation, call reset yourself.

```python
from body import Service
class MyService(Service):
  def __init__(self):
    self.reset()
  def reset():
    # setup
```

It is entirely up to you what reset can and can't do in your service. You are
only required to provide it, and could easily do the following and still be
considered a valid `Service`
```python
from body import Service
class MyService(Service):
  def reset():
    pass
```

[ [top](#body), [contents](#contents), [service](#service) ]

### Requests
Requests are the part that interfaces like REST connect to and export to
whatever client they represent. They always receive a single argument called
`req`, must return a `Response`, and must follow a specific format for naming
in order to be exported.

#### Format
In order for a method in a service to be available to other services, it's
required to keep a specific format. It can not contain any characters except
those between the letter 'a' and the letter 'z'. Underscores may be used between
letters, but can not end or start a request, it must then end with one of the
following `_create`, `_read`, `_update`, or `_delete`.

The following are all valid request methods.
```python
from body import Service
class MyService(Service):
  reset():
    pass

  # POST user
  def user_create(self, req: jobject) -> Response:
    pass

  # DELETE user
  def user_delete(self, req: jobject) -> Response:
    pass

  # GET user
  def user_read(self, req: jobject) -> Response:
    pass

  # PUT user
  def user_update(self, req: jobject) -> Response:
    pass

  # GET users/by/id
  def users_by_id_read(self, req: jobject) -> Response:
    pass

  # DELETE users/by/category
  def users_by_category_delete(self, req: jobject) -> Response:
    pass

  # GET search/users
  def search_users_read(self, req: jobject) -> Response:
    pass

  # PUT a
  def a_update(self, req: jobject) -> Response:
    pass
```

[ [top](#body), [contents](#contents), [service](#service),
[requests](#requests) ]

#### req
`req` contains information about the request. It can contain

`data` which is any valid JSON data.

`session` an instance of a [Memory](https://pypi.org/project/memory-oc/)

`environment` a `dict` of environment variables, see
[Bottle](https://bottlepy.org/docs/dev/tutorial.html#wsgi-environment).

[ [top](#body), [contents](#contents), [service](#service),
[requests](#requests) ]

#### Response
All request methods must return a `Response` instance. See the
[documentation](#response--error) on `Response` and `Error` for more info.

[ [top](#body), [contents](#contents), [service](#service),
[requests](#requests) ]