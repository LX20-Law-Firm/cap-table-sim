import unittest
from fractions import Fraction as F

from cap_table_sim.core import Instrument, simulate_round


class RoundTests(unittest.TestCase):
    def test_two_rounds(self):
        first = simulate_round({"Founder": 1000}, 10000, 2500, investor="A")
        self.assertEqual(first.ownership["A"], F(1, 5))
        second = simulate_round(first.holdings, 25000, 5000, investor="B")
        self.assertEqual(second.ownership["Founder"], F(2, 3))
        self.assertEqual(sum(second.ownership.values()), 1)

    def test_cap_discount_and_multiple_conversion_order(self):
        instruments = [
            Instrument("A", 1000, cap=5000, discount="0.2"),
            Instrument("B", 1000, discount="0.2"),
            Instrument("C", 1000, cap=20000),
        ]
        result = simulate_round({"Founder": 1000}, 10000, 2000, instruments)
        reverse = simulate_round({"Founder": 1000}, 10000, 2000, instruments[::-1])
        self.assertEqual(result.holdings, reverse.holdings)
        self.assertEqual(result.holdings["A"], 200)
        self.assertEqual(result.holdings["B"], 125)
        self.assertEqual(result.holdings["C"], 100)
        self.assertEqual(result.new_investor_units, 200)
        self.assertEqual(sum(result.ownership.values()), 1)

    def test_simple_interest_note(self):
        note = Instrument("Note", 1000, discount="0.2", annual_interest="0.1", years=2, kind="note")
        result = simulate_round({"Founder": 1000}, 10000, 0, [note])
        self.assertEqual(result.holdings["Note"], 150)
        self.assertEqual(result.conversions[0].price, 8)

    def test_pre_and_post_pool_added_in_round(self):
        pre = simulate_round({"Founder": 1000}, 10000, 2500, pool_target="0.2")
        post = simulate_round({"Founder": 1000}, 10000, 2500, pool_target="0.2", pool_timing="post")
        self.assertEqual(pre.pool_added, F(1000, 3))
        self.assertEqual(pre.round_price, F(15, 2))
        self.assertEqual(pre.pool_fraction, F(1, 5))
        self.assertEqual(pre.ownership["New investor"], F(1, 5))
        self.assertEqual(post.pool_added, F(625, 2))
        self.assertEqual(post.round_price, 10)
        self.assertEqual(post.pool_fraction, F(1, 5))
        self.assertEqual(post.ownership["New investor"], F(4, 25))

    def test_pool_and_multiple_conversions(self):
        result = simulate_round(
            {"Founder": 900, "Employee pool": 100},
            10000,
            2000,
            [Instrument("A", 1000, cap=5000), Instrument("A", 1000, discount="0.2")],
            pool_target="0.2",
        )
        self.assertEqual(result.pool_fraction, F(1, 5))
        self.assertEqual(len(result.conversions), 2)
        self.assertEqual(sum(result.ownership.values()), 1)
        self.assertEqual(result.holdings["A"], sum(c.units for c in result.conversions))

    def test_pool_never_shrinks(self):
        result = simulate_round({"Founder": 500, "Employee pool": 500}, 10000, 0, pool_target="0.1")
        self.assertEqual(result.pool_added, 0)
        self.assertEqual(result.pool_fraction, F(1, 2))

    def test_rounding_and_residuals(self):
        result = simulate_round({"Founder": 3}, 10, 1, [Instrument("A", 1)], quantum=1)
        self.assertEqual(result.new_investor_units, 0)
        self.assertEqual(result.unallocated_cash, 1)
        self.assertEqual(result.conversions[0].unconverted_amount, 1)
        quota = simulate_round({"Founder": 3}, 10, 1, quantum="0.01", unit="SRL quota units")
        self.assertEqual(quota.new_investor_units, F(3, 10))
        rounded = simulate_round({"Founder": 1000}, 10000, 2500, pool_target="0.2", quantum=1)
        self.assertEqual(rounded.pool_added, 333)
        self.assertNotEqual(rounded.pool_fraction, F(1, 5))

    def test_invalid_inputs(self):
        options = [
            dict(pre_money=0),
            dict(investment=-1),
            dict(pool_target=1),
            dict(pool_target="0.9", investment=10000),
            dict(quantum=0),
            dict(quantum=3),
            dict(unit="other"),
            dict(pool_timing="other"),
            dict(pre_money="NaN"),
            dict(investment=0.1),
            dict(instruments=[Instrument("A", 1, discount=1)]),
            dict(instruments=[Instrument("A", 1, cap=0)]),
            dict(instruments=[Instrument("A", 1, annual_interest="0.1")]),
        ]
        for option in options:
            kwargs = dict(pre_money=10000, investment=0)
            kwargs.update(option)
            with self.subTest(option=option), self.assertRaises(ValueError):
                simulate_round({"Founder": 1000}, **kwargs)
        with self.assertRaises(ValueError):
            simulate_round({}, 10, 0)


if __name__ == "__main__":
    unittest.main()
