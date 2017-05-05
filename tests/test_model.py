import unittest
from pso.models import BaseModel
from pso.fields import BaseField
from pso.query import BaseQuerySet


class TestModel(unittest.TestCase):

    def test_010_create_model(t):
        "Create model. (check Fields & Descriptor)"

        class TestModel(BaseModel):

            field1 = BaseField(store=True)
            field2 = BaseField(multi_valued=True)
            field3 = BaseField(store=False)

            other_prop = "qwerty"

        t.assertEqual(TestModel._fields, ['field1', 'field2', 'field3'])
        t.assertEqual(TestModel._stored_fields, ['field1'])
        t.assertIsInstance(TestModel.objects, BaseQuerySet)

    def test_020_multivalued_from_list(t):
        "Create multivalued field from [Field()]"

        class TestModel(BaseModel):
            field1 = [BaseField(multi_valued=False)]

        t.assertEqual(TestModel.field1.multi_valued, True)

    def test_030_model_values(t):
        "Get&Set Model fields values"

        class TestModel(BaseModel):
            field1 = [BaseField(store=True)]
            field2 = BaseField(store=True)
            field3 = BaseField()

        values = {
            'field1': ['val1.1', 'val1.2', 'val1.3'],
            'field2': 'val2',
            'field3': 'val3',
        }
        model1 = TestModel(**values)

        t.assertDictEqual(values, dict(model1))
        for k, v in values.items():
            t.assertEqual(
                v, getattr(model1, k),
                msg='Error when get value by field descriptor'
            )
