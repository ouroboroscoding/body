# body_oc releases

## 2.0.3
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