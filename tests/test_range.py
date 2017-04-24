import unittest
from pso.q import Range
from pso.q import NoValue


r1 = Range(-99, 10, True, True)
r2 = Range(-10, 99, True, True)
r3 = Range(10, 15, False, False)
r4 = Range(15, 17, True, False)
r5 = Range(15, 17, False, False)
r6 = Range(fr=-10, fr_incl=True)
r7 = Range(fr=10)
r8 = Range(to=-10, to_incl=True)
r9 = Range(to=10, to_incl=True)


class TestRange(unittest.TestCase):

    def test_010_create_range(t):
        "Range creating"
        t.assertEqual(Range(-1, 10), (-1, 10, False, False))
        t.assertEqual(Range(fr=99, fr_incl=True), (99, NoValue, True, False))
        t.assertEqual(Range(to=99, to_incl=True), (NoValue, 99, False, True))

    def test_020_create_range_from_native(t):
        "Range from native python range()"
        t.assertEqual(Range.from_range(range(0, 10)), (0, 10, False, False))
        t.assertEqual(
            Range.from_range(range(0, 10, True)), (0, 10, True, True))

    def test_030_overlap_detection(t):
        "Overlap detection"
        t.assertTrue(r1._check_overlap(r2), msg="Fatal. No overlap detection")
        t.assertTrue(r3._check_overlap(r4), msg="Equal and inclusive")
        t.assertTrue(r3._check_overlap(r1), msg="Equal and inclusive")
        t.assertFalse(r3._check_overlap(r5), msg="Equal, but exclusive")
        t.assertFalse(r1._check_overlap(r4), msg="Equal, but exclusive")
        t.assertFalse(r1._check_overlap(r4), msg="Without any overlap.")

    def test_040_test_overlap_or_merge(t):
        "Merging overlapped Ranges with OR (Union)"
        t.assertEqual(r1 | r2, Range(-99, 99, True, True))
        t.assertEqual(r1 | r3, Range(-99, 15, True, False))
        t.assertEqual(r3 | r4, Range(10, 17, False, False))
        t.assertEqual(r6 | r7, Range(-10, NoValue, True, False))

        # BUG with NoValue.
        t.assertEqual(r6 | r9, Range(-10, 10, True, True))

    def test_050_test_overlap_and_merge(t):
        "Merging overlapped Ranges with AND (Intersection)"
        t.assertEqual(r1 & r2, Range(-10, 10, True, True))
        t.assertEqual(r4 & r5, r5)

        # Here, works fine.
        t.assertEqual(r6 | r9, Range(-10, 10, True, True))
