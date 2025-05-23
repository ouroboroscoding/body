# body_oc releases

## 2.2.0
- Removed docs and body-docs script, currently being worked on in an independant module called `body_docs`.
- Added a system for adding key / value pairs to requests that can be passed directly, or via X-* headers.
- Removed the ability to set headers and access bottle.request / bottle.response in order to decouple Body and the requests from knowing they are being called via HTTP, or from within the same process, or any other way created in the future.

## 2.1.2
- Fixed issue with using `__list` in multi-service script where only the first service had the correct url assigned.

## 2.1.1
- Made a fix for the URI generated to map internal service instance nouns. Prior to this fix, it was only possible to run multiple services in a single node if they didn't interact with each other.

## 2.1.0
- Removed `register_services` as data is generated automatically.
- Added `rest` method on `Service` to automatically create a `REST` instance using the instance of the `Service`.

## 2.0.3
- Updated LICENSE.
- Added `EMPTY_TUUID` to `constants.py`
- Added `__all__` to `errors.py` that exports everything that's an int.
- `body-docs` will now allow single spaces in section names, and those spaces are replaced with underscores in the returned parser object.
- `body-docs` will now ignore any line that starts with - and ends with -, good for marking lines which look like sections but aren't.

## 2.0.2
- Added the `check_data` method to `Service`.
- Added the `body-doc` cli script to generate rest documentation for `Service`s.

## 2.0.1
- Added check in rest to make sure "allowed" domains is a list.
- Fixed bug in init where .id() was being called on the session instead of .key().