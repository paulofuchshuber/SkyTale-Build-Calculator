from tests import test_aggregate
import traceback

tests = [
    test_aggregate.test_range_plus_range_strength,
    test_aggregate.test_single_plus_range_talent_inside,
    test_aggregate.test_single_plus_range_talent_above,
    test_aggregate.test_single_plus_range_talent_below,
    test_aggregate.test_stats_sum_min_max,
]

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
