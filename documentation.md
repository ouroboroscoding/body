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
- [Calling other Services](#calling-other-services)
- [Constants](#constants)
- [Error Codes](#error-codes)
- [Regular Expressions](#regular-expressions)
- [Request](#request)
- [Response & Error](#response--error)
- [ResponseException](#responseexception)
- [REST](#rest)
- [Service](#service)

## Module Install

### Requires
body_oc requires python 3.10 or higher

### Install via pip
```bash
pip install body_oc
```

[ [top](#body_oc) / [contents](#contents) ]

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
    "logging": {
      "level": "info",
      "output": "file",
      "pretty_print": false,
      "file": {
        "backups": 30,
        "name": "{name}.log",
        "path": "/var/log/services"
      },
      "names": {
        "rest": {
          "level": "error",
          "file": {
            "backups": 5
          }
        }
      }
    },
    "rest": {
      "allowed": [ "mydomain.com" ],
      "cookie": "session",
      "default": {
        "domain": "localhost",
        "host": "0.0.0.0",
        "protocol": "http"
      },
	  "monitor": [ "admin", "Gcg6sKMY" ],
      "services": {
        "myservice": { "port": 8000, "workers": 10 },
        "myotherservice": { "port": 8001, "workers": 2 }
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

[ [top](#body_oc) / [contents](#contents) /
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

[ [top](#body_oc) / [contents](#contents) /
[module configuration](#module-configuration) /
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

[ [top](#body_oc) / [contents](#contents) /
[module configuration](#module-configuration) /
[configuration sections](#configuration-sections) ]

#### body section
```json
  "body": {
    "logging": {
      "level": "info",
      "output": "file",
      "pretty_print": false,
      "file": {
        "backups": 14,
        "name": "{name}.log",
        "path": "/var/log/services"
      },
      "names": {
        "rest": {
          "level": "error",
          "file": {
            "backups": 7
          }
        }
      }
    },
    "rest": {
      "allowed": [ "mydomain.com" ],
      "cookie": "session",
      "default": {
        "domain": "localhost",
        "host": "0.0.0.0",
        "protocol": "http"
      },
      "monitor": [ "admin", "Gcg6sKMY" ],
      "services": {
        "myservice": { "port": 8000, "workers": 10 },
        "myotherservice": { "port": 8001, "workers": 2 }
      }
    }
  }
```

#### body.logging
Handles all the logging specific configuration like number of backups and paths
for files.

##### body.logging.output
`output` has 3 different values: "file", "stdout", and "stderr". For production
it's best to set it to "file" so that we store everything in log files by day
that can be deleted when there's too many of them. However if you want to watch
the output live during development, or you want to manage the log files yourself
in production, you can use "stdout" / "stderr" to output to the console or
whatever tool you pipe to the appropriate stream.

The default for `output` is "stdout".

##### body.logging.level
`level` controls what log info actually gets sent out. Level has 5 different
values in order of: "debug", "info", "warning": "error", "critical". What this
means is that whatever level you choose, you will see it and everything to the
left of it. Choose "debug" and you will see every single message. Pick "warning"
and you will see warnings, errors, and critical messages.

The default for `level` is "info".

##### body.logging.pretty_print
By default log files are meant to be one issue per line of the file. This is
great if that file is parse by another program, or you write your own parser,
but if you're watching output live while debugging, or you have no intention of
having the logs parsed by another script, having data printed in a nice human
readable "pretty" format can be a real blessing. Set `pretty_print` to `true`
to see things like

```json
2026-10-20 15:29:27.185491 [INFO] REQUEST __list {
  "data": [
    "/access",
    [
      "/account",
      {
        "_id": "2a096f9272da11f0af9335bc0e1334cd"
      }
    ]
  ]
}
```

instead of

```json
2026-10-20 15:29:27.185491 [INFO] REQUEST __list { "data": [ "/access", [ "/account", { "_id": "2a096f9272da11f0af9335bc0e1334cd" } ] ] }
```

##### body.logging.file
`file` is only applicable when you choose "file" for `output`. It controls where
files are stored, under what name, and how many backups are made.

`file.path` controls the directory where the log files will be placed. It can
have an ending slash or not.

The default value is `"./"`, the current directory your script is being run
from.

`file.name` controls the template used to name log files. The "{name}" variable
corresponds to the name of the log file being created, in the case of services,
this is the name of the service in lowercase, i.e. `class MyService` is
"myservice". REST creates its own log using "rest".

The default value is `"{name}.log"`.

`file.backups` controls the number of days of backups to keep. The current log
will use the `file.name` template, subsequent files will use the data the file
corresponds to. i.e. "myservice.log", "myservice.log.2026-10-18",
"myservice.log.2026-10-17", etc.

The default value is `30`.

##### body.logging.names
Used to override default values for specific log files. For example, maybe since
"rest" is not really relevant data, most of the time we just want to see
"errors" and we don't need as many backups, only 1 week instead of the normal 2.
Anything that is listed in `body.logging` can be added to `names` in order to
override it for that specific log name.

#### body.rest
Handles all the REST specific configuration like CORS, cookies, and hostname and
ports.

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

##### body.rest.cookie
Represents the name of the cookie checked for a session key. Body can activate
sessions via the Authorization header, but it can also check a cookie. Setting a
name here will let it know which cookie to check, otherwise it will skip
checking for cookie and go straight to `Authorization`.

[ [top](#body_oc) / [contents](#contents) /
[module configuration](#module-configuration) /
[configuration sections](#configuration-sections) /
[body section](#body-section) ]

##### body.rest.monitor
If set, adds a `/__monitor` request to the server accessible using the `user`
(first string) and `password` (second string) which provides details about the
currently running server.

```json
      "monitor": [ "admin", "Gcg6sKMY" ],
```

If you would rather use a different URI set the third element

```json
      "monitor": [ "admin", "Gcg6sKMY", "my_monitor_uri" ],
```

And this will set `https://admin:Gcg6sKMY@localhost:8000/my_monitor_uri` as the
monitor endpoint for "myservice".

##### body.rest.services
In order to know how to both run and connect to
[body_oc](https://pypi.org/project/body_oc/) services, we need to indicate,
what protocol, domain, and port to use to connect, what interface they will
respond to, and how many instances of each we can spin up.

In this instance we have two services, **myservice** and **myotherservice**.
**myservice** is available at `http://localhost:8000` and will be running 10
threads that will be listening on ip `0.0.0.0`, or internal only traffic.
**myotherservice** is available at `http://localhost:8001` and will be running 2
threads that will also be listening on ip `0.0.0.0`.

We are relying on the defaults to generate some of the data, and this is a very
simplistic initial launch setup. As we launch more servers and spread the load,
you might have the config on the **myservice** server be something more like
this where **myotherservice** is running on another server inside the network.
```json
      "services": {
        "myservice": {
          "domain": "localhost",
          "host": "192.168.0.1",
          "port": 80,
          "protocol": "http",
          "workers": 10
        },
        "myotherservice": {
          "domain": "myotherservice.mydomain",
          "port": 80,
          "protocol": "http"
        }
      }
```
...or like this, where it's running outside the network
```json
        "myotherservice": {
          "domain": "myotherservice.mydomain.com",
          "port": 443,
          "protocol": "https"
        }
```

[ [top](#body_oc) / [contents](#contents) /
[module configuration](#module-configuration) /
[configuration sections](#configuration-sections) /
[body section](#body-section) ]

## Calling other Services
`body.request` Handles making a request to another service.

```python
import body
response = body.request(
  'myservice', 'create', 'user', { 'data': { 'record':  {} } }
)
```

We are calling the 'create' action on the 'myservice' service at the noun
'user', and passing it data and no session.

### body.create
Shortcut for calling [request](#bodyrequest) with the `create` action.
```python
response = body.create(
  'myservice', 'user', { 'data': { 'record': { } } }
)
```

[ [top](#body_oc) / [contents](#contents) /
[calling other services](#calling-other-services) ]

### body.delete
Shortcut for calling [request](#bodyrequest) with the `delete` action.
```python
response = body.delete(
  'myservice', 'user', { 'data': { '_id': 'someid' } }
)
```

[ [top](#body_oc) / [contents](#contents) /
[calling other services](#calling-other-services) ]

### body.read
Shortcut for calling [request](#bodyrequest) with the `read` action.
```python
response = body.read(
  'myservice', 'user', { 'data': { '_id': 'someid' } }
)
```

[ [top](#body_oc) / [contents](#contents) /
[calling other services](#calling-other-services) ]

### body.update
Shortcut for calling [request](#bodyrequest) with the `update` action.
```python
response = body.update(
  'myservice', 'user', { 'data': { '_id': 'someid', 'record': { } } }
)
```

[ [top](#body_oc) / [contents](#contents) /
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
SECONDS_30_DAYS = 2592000
SECONDS_365_DAYS = 31536000
```

[ [top](#body_oc) / [contents](#contents) ]

## Error Codes
Exports errors as unsigned integer constants

Errors related to http/https requests
```python
REST_REQUEST_DATA = 100
REST_CONTENT_TYPE = 101
REST_AUTHORIZATION = 102
REST_LIST_TO_LONG = 103
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

[ [top](#body_oc) / [contents](#contents) ]

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

[ [top](#body_oc) / [contents](#contents) ]

## Request
`Request` is the class passed to all request paths on Services as well as when
[calling other services](#calling-other-services).

It can optionally contain any of the 3 following members:

### Request.data
This is the main data passed to requests and is stored using a [jobject](https://pypi.org/project/jobject/).
When passed via REST it is sent as the body of the message using JSON and so
must confirm to data that can be converted to and from JSON.

### Request.session
This is the session data passed to requests. It is stored using [Memory](https://pypi.org/project/memory-oc/).
When passed via REST it is sent as a key either in a [cookie](#bodyrestcookie)
or in the `Authorization` header.

### Rquest.meta
This is meta data passed to requests and is stored using a [jobject](https://pypi.org/project/jobject/).
When passed via REST it is sent as `X-Body-[key]` headers so values must be
strings or be able to be converted to strings. Note that the receiving end will
always end up with strings if received via REST.

## Response & Error
`Response` is the class returned from all [Service](#service) requests. It
contains 3 parts, [data](#responsedata) / [error](#responseerror), and
[warning](#responsewarning).

### Response.data
The first argument to the Response constructor is `data` related to the request.
It can be considered a valid response to the request. Here we are returning a
list of records from a READ / GET request.

```python
from body import Request, Response, Service
class MyService(Service):
  def my_request_read(self, req: Request) -> Response:
	return Response([ """ records """ ])
```

Here we are returning a simple boolean based on a record existing or not
```python
from body import Request, Response, Service
from records.user import User
class MyService(Service):
  def my_request_exists_read(self, req: Request) -> Response:
	self.check_data(req.data, [ '_id' ])
	return Response(
	  User.exists(req.data._id)
	)
```

[ [top](#body_oc) / [contents](#contents) / [response & error](#response--error) ]

### Response.error
The second argument to Response is `error`, traditionally composed of a `code`
and a `msg`.

Here we are trying to find a user record based on its ID, if the DB can't find
anything, we return only an error with the `code` DB_NO_RECORD, and the `msg`
as a list with the ID that failed and the record type that it failed for.

```python
from body import errors, Request, Response, Service
from records.user import User
class MyService(Service):
  def my_request_read(self, req: Request) -> Response:
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
from body import Error, errors, Request, Response, Service
from records.user import User
class MyService(Service):
  def my_request_read(self, req: Request) -> Response:
	self.check_data(req.data, [ '_id' ])
	user = User.get(req.data._id)
	if not user:
	  return Error(
		errors.DB_NO_RECORD,
		[ req.data._id, 'user' ]
	  )
	return Response(user)
```

[ [top](#body_oc) / [contents](#contents) / [response & error](#response--error) ]

### Response.warning
The third argument to Response is helpful if the request is successful, but with
caveats. Perhaps that user account was created, but the e-mail notifying the
account creator didn't get sent, an error by itself, but not with the primary
action. Or perhaps you are returning the data requested, but you add a warning
that it, the data, is out of date at the moment.

```python
from body import Request, Response, Service
from records.user import User
from em import send
class MyService(Service):
  def my_request_create(self, req: Request) -> Response:
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

[ [top](#body_oc) / [contents](#contents) / [response & error](#response--error) ]

## ResponseException
`ResponseException` is useful if you need to call other functions in your
request methods that themselves will generate the `Response` or `Error`.
This is especially helpful for errors.

```python
from body import errors, Request, Response, ResponseException, Service
class MyService(Service):

  @classmethod
  def _my_method(cls, _id):
	raise ResponseException(
	  error=(errors.ALREADY_DONE, 'we did it already')
	)

  def my_service_create(self, req: Request) -> Response:
	self.check_data(req.data, [ '_id' ])
	self._my_method(req.data._id)
	return Response(True)
```

We don't need to check the response to `_my_method` in `my_service_create`
because it will raise a `ResponseException` which will bubble up into
[REST](#rest), or some other interface, and be handled as if it was a normal
`Response` being returned to the client.

## REST
The `rest` method provides a way to take a service and connect it to the
internet via http requests. It uses the services request methods and connects
them to the appropriate POST / GET / PUT / DELETE methods.

When using body as a REST server, you MUST make sure to monkey patch gevent as
the first thing in your code. Nothing else can run / be imported before the
`patch_all()` call

```python
from gevent import monkey
monkey.patch_all()

from body import Request, Response, Service
import config

class MyService(Service):
  def reset():
	pass
  def my_request_create(self, req: Request) -> Response:
	return Response(id)
  def my_request_delete(self, req: Request) -> Response:
	return Response(True)
  def my_request_read(self, req: Request) -> Response:
	return Response(user)
  def my_request_update(self, req: Request) -> Response:
	return Response(True)

def errors(error):
  # Available on every request
  for k in [ 'traceback', 'method', 'service', 'path' ]:
	print('%s: %s' % ( k, str(error[k]) ))
  # Request dependant
  for k in [ 'data', 'session', 'environment' ]:
	if k in error:
	  print('%s: %s' % ( k, str(error[k]) ))

# Only run if called directly
if __name__ == '__main__':
	MyService().rest(
		on_errors = errors
	)
```

Here we have created a service, `MyService` with one noun `my/request` that
responds to all 4 methods, meaning all the following would be valid:

`POST my/request`\
`DELETE my/request`\
`GET my/request`\
`PUT my/request`

### Low level http
`rest` uses [Bottle](https://bottlepy.org/docs/dev/) as the underlying sytem for
adding http functionality. If you want more direct access to the underlying
system you can create `REST` directly and get access to the http server instance

```python
from body.rest import REST
REST(
	[ MyService ],
	on_errors = errors
).run(
	host = '127.0.0.1',
	port = 80,
	workers = 2,
	timeout = 30
)
```

[ [top](#body_oc) / [contents](#contents) ]

## Service
`Service` is the class all services should extend. It has several helper
methods, one abstract method, and a specific format for any other method which
the user wants to make available to REST, CLI, or some other interface.

### additional_routes

We can add simple [Bottle](https://bottlepy.org/docs/dev/routing.html#explicit-routing-configuration)
routes to our services that will automatically be added to any call to REST that
uses the instance. This includes adding the necessary service prefix, and the
OPTIONS type to the methods.

```python
def test_route():
	print(request.query)
	return '<html />'

MyService.additional_routes = [
	( '/test', 'GET', test_route )
]
```

or

```python
def test_route():
	print(request.query)
	return '<html />'

class MyService(Service):
	additional_routes = [
		( '/test', 'GET', test_route )
	]
```

or even

```python
class MyService(Service):

	def __init__(self):
		super(MyService, self).__init__()
		self.additional_routes = [
			( '/test', 'GET', self.test_route )
		]

	def test_route():
		print(request.query)
		return '<html />'
```

[ [top](#body_oc) / [contents](#contents) / [service](#service) ]

### check_data
The `check_data` method is a helper for checking the input to any request
exists before trying to use it.

```python
from body import errors, Request, Response, Service
from records.user import User
from records.permissions import Permissions
class MyService(Service):

  def my_request_create(self, req: Request) -> Response:

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

[ [top](#body_oc) / [contents](#contents) / [service](#service) ]

### log
Used internally to log requests and their responses, but can also be called
with different log levels by your own services. This is helpful if you don't
want to have to create your own log.

```python
from body import Error, LogLevel, Request, Service

class MyService(Service):
	def always_error_read(self, req) -> Response:
		self.log(LogLevel.ERROR, 'This is an error log')
		return Error(DATA_FIELDS, [ [ '_id', 'missing' ] ])
```

See [LogLevel](#loglevel) for all possible types.

[ [top](#body_oc) / [contents](#contents) / [service](#service) ]

### reset
Called when the service(s) are started and when they are sent a reset request.
It's best to do any setup here.

```python
from body import Service
class MyService(Service):
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

[ [top](#body_oc) / [contents](#contents) / [service](#service) ]

### rest
`rest` is a shortcut for starting a single service with `REST`. It will use the
data from the config.rest section to know how to setup the `host`, `port`
and other things like `CORS`.

When used be sure to do the `gevent` monkey patch as the first thing in your
file or you might have issues.

```python
if __name__ == '__main__':
	from gevent import monkey
	monkey.patch_all()

from body import Request, Response, Service

class MyService(Service):
	"""My Service"""

	def user_create(self, req: Request) -> Response:
		"""Create a user"""
		pass

	def user_read(self, req: Request) -> Response:
		"""Read a user"""
		pass

if __name__ == '__main__':
	Admin.rest()
```

[ [top](#body_oc) / [contents](#contents) / [service](#service) ]

### service_name
Returns the name of the service all in lowercase which is how it's identified by
REST and any other external calls like `create`, `delete`, `read`, and `update`.

```python
from body import Service
class MyService(Service):
  def reset():
	pass

# prints "myservice"
print(MyService.service_name())
```

[ [top](#body_oc) / [contents](#contents) / [service](#service) ]

### shutdown
If for some reason you instantiate any of the Services yourself, rather than
going through `REST` AND you have logging enabled, you MUST call this before
your app / script closes if you want to gaurantee everything is written to the
log.

```python
from body import Service
class MyService(Service):
  def reset():
	pass

my_service = MyService()

# ... do stuff ...

my_service.shutdown()
```

### Service Requests
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
from body import Request, Service
class MyService(Service):
  reset():
	pass

  # POST user
  def user_create(self, req: Request) -> Response:
	pass

  # DELETE user
  def user_delete(self, req: Request) -> Response:
	pass

  # GET user
  def user_read(self, req: Request) -> Response:
	pass

  # PUT user
  def user_update(self, req: Request) -> Response:
	pass

  # GET users/by/id
  def users_by_id_read(self, req: Request) -> Response:
	pass

  # DELETE users/by/category
  def users_by_category_delete(self, req: Request) -> Response:
	pass

  # GET search/users
  def search_users_read(self, req: Request) -> Response:
	pass

  # PUT a
  def a_update(self, req: Request) -> Response:
	pass
```

[ [top](#body_oc) / [contents](#contents) / [service](#service) /
[requests](#service-requests) ]

#### req
`req` contains information about the request. See the [documentation](#request)
on `Request` for more info.

[ [top](#body_oc) / [contents](#contents) / [service](#service) /
[requests](#service-requests) ]

#### Response
All request methods must return a `Response` instance. See the
[documentation](#response--error) on `Response` and `Error` for more info.

[ [top](#body_oc) / [contents](#contents) / [service](#service) /
[requests](#service-requests) ]