import pytest

from satellite.parallel import DPLL
from satellite.examples.queens import Queens
from satellite.expr import And, Or, var
from satellite.tseitin import Tseitin
from satellite.utils import numbered_var

w, x, y, z = var("w x y z")


class TestDPLL:
    def test_find_units(self) -> None:
        expr = (w | x) & Or(y) & (y | z)
        assert DPLL.find_units(expr) == {y}

        expr = (w | x) & Or(~y) & (y | z)
        assert DPLL.find_units(expr) == {~y}

        expr = (w | x) & (y | z)
        assert DPLL.find_units(expr) == set()

    def test_unit_propagate(self) -> None:
        expr = (w | x) & Or(y) & (y | z) & (z | ~y)
        expected = (w | x) & Or(z)
        assert DPLL.unit_propagate({y}, expr) == expected

    def test_find_pure(self) -> None:
        assert DPLL.find_pure((w | x) & (y | z)) == {w, x, y, z}
        assert DPLL.find_pure((w | ~w) & (y | ~z)) == {y, ~z}

    def test_pure_literal_assign(self) -> None:
        assert DPLL.pure_literal_assign(y, (w | ~w) & (y | z)) == And(w | ~w)
        assert DPLL.pure_literal_assign(~x, (w | ~w) & (y | z) & (w | ~x)) == (
            w | ~w
        ) & (y | z)

    @pytest.mark.parametrize(
        "and_expr",
        (
            And(Or(x)),
            And(Or(~x)),
            And(x | y),
            And(x | x),
            And(x | ~x),
            And(~x | ~x),
        ),
    )
    def test_dpll_sat(self, and_expr: And) -> None:
        assert DPLL(and_expr).check()

    @pytest.mark.parametrize(
        "and_expr",
        (And(Or(x), Or(~x)),),
    )
    def test_dpll_unsat(self, and_expr: And) -> None:
        assert not DPLL(and_expr).check()


def test_queens() -> None:
    queens = Queens(2)
    queens_formula = queens.get_formula()

    tseitin = Tseitin(queens_formula, rename_vars=False, name_gen=numbered_var("x", 0))
    queens_cnf = tseitin.transform(sort=True)

    assert not DPLL(queens_cnf).check()