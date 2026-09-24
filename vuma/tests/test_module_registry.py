
import unittest

from vuma.api.v1.modules import (
    MODULE_REGISTRY,
)


class TestVumaModuleRegistry(unittest.TestCase):
    def test_registry_not_empty(self):
        self.assertTrue(MODULE_REGISTRY)

    def test_expected_module_count(self):
        self.assertEqual(
            len(MODULE_REGISTRY),
            21,
        )

    def test_module_codes_unique(self):
        codes = list(MODULE_REGISTRY.keys())

        self.assertEqual(
            len(codes),
            len(set(codes)),
        )

    def test_every_module_has_screens(self):
        for code, module in MODULE_REGISTRY.items():
            self.assertTrue(
                module["screens"],
                msg=f"{code} has no screens",
            )

    def test_sales_mapping(self):
        sales = MODULE_REGISTRY["SAL"]

        self.assertEqual(
            sales["screens"]["Customers"],
            "Customer",
        )

        self.assertEqual(
            sales["screens"]["Sales Orders"],
            "Sales Order",
        )

    def test_inventory_mapping(self):
        inventory = MODULE_REGISTRY["INV"]

        self.assertEqual(
            inventory["screens"]["Items"],
            "Item",
        )

        self.assertEqual(
            inventory["screens"]["Warehouses"],
            "Warehouse",
        )
