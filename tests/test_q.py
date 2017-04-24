"""
You can not simply test value of Q, because each of
those operators is overloaded and produce new Q instead of result.

AssertEqueal and other methods simply doesn't work
"""
import unittest
from pso.q import Range
from pso.q import Q
from pso.q import NoValue
from pso.q import Condition
from pso.q import Operator

q1 = ('field2', None, NoValue, Q.DEFAULT_OPERATOR, False, (), 1)
q2 = ('field1', Condition.LT, 999, Q.DEFAULT_OPERATOR, False, (), 1)
q3 = ('field3', None, NoValue, Q.DEFAULT_OPERATOR, False, (), 1)
q4 = (None, None, None, Q.DEFAULT_OPERATOR, False, (q1, q2, q3), 1)


def make_kw(tpl):
    return dict(zip(Q._fields, tpl))


def q_range(rng):
    return ('field1', Condition.RANGE, rng,
            Q.DEFAULT_OPERATOR, False, (), 1)


class TestQ(unittest.TestCase):

    def test_010_create(t):
        "Creating of Q objects"
        t.assertEqual(q2, tuple(Q(field1__lt=999)),
                      msg="Can no create Q from kwargs")
        t.assertEqual(q1, tuple(Q('field2')),
                      msg="Can not create field-only Q")
        t.assertEqual(q1, tuple(Q(*q1)),
                      msg="Can not create Q from tuple")
        t.assertEqual(q1, tuple(Q(**make_kw(q1))),
                      msg="Can not create Q from kwargs")

    def test_020_create_aggregation(t):
        "Create aggregation Q of Q objects"
        query1 = Q(field1=999)
        query2 = Q(field2_gte=15)
        query3 = Q(field1=17)

        t.assertEqual(
            [tuple(q) for q in Q(query1, query2, query3).childs],
            [tuple(query1), tuple(query2), tuple(query3)],
            msg="Nested elements are wrong"
        )

        t.assertEqual(
            Q(Operator.AND, query1, query2, query3).operator,
            Operator.AND, msg="Error while create Q with Operator as args[0]"
        )

    def test_040_comparison_overloading(t):
        "Overloading <, <=, >, >= operators"
        t.assertNotEqual(
            q2, tuple(Q('field1') < 999),
            msg="convertation to Range is broken."
        )

        msg = "Q.__{}__ doesn't work.".format

        t.assertEqual(
            q_range(Range(fr=100, fr_incl=False)),
            tuple(Q('field1') > 100), msg=msg('gt')
        )

        t.assertEqual(
            q_range(Range(fr=100, fr_incl=True)),
            tuple(Q('field1') >= 100), msg=msg('ge')
        )

        t.assertEqual(
            q_range(Range(to=100, to_incl=False)),
            tuple(Q('field1') < 100), msg=msg('lt')
        )

        t.assertEqual(
            q_range(Range(to=100, to_incl=True)),
            tuple(Q('field1') <= 100), msg=msg('le')
        )

    def test_050_q_range_merge(t):
        "Merging Ranges in Q objects"

        t.assertEqual(
            q_range(Range(fr=17, to=100, fr_incl=False, to_incl=True)),
            tuple((Q('field1') <= 100) > 17),
            msg="Range merge Err. (Q > 17 ) <= 100"
        )

    @unittest.skip("Need compact childs grouped by field on merge_condition.")
    def test_060_aggregate_by_logical_operators(t):
        "Create aggregations by & - AND, | - OR operators"
        qs = (Q('field1') >= 17) | (Q('field2') == "SomeText") | (Q('field1') >= 19)
        print(qs)
        raise ValueError()
