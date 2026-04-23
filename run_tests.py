from tests import test_aggregate
import traceback, inspect

# collect all callables in test_aggregate starting with 'test_'
tests = []
for name, obj in inspect.getmembers(test_aggregate):
    if name.startswith('test_') and inspect.isfunction(obj):
        tests.append(obj)

failed = []
for t in tests:
    try:
        t()
        print(f"OK: {t.__name__}")
    except AssertionError:
        print(f"FAIL: {t.__name__}")
        traceback.print_exc()
        failed.append(t.__name__)
    except Exception:
        print(f"ERROR: {t.__name__}")
        traceback.print_exc()
        failed.append(t.__name__)

if failed:
    print('\nSome tests failed:', failed)
    raise SystemExit(1)
else:
    print('\nAll tests passed')
