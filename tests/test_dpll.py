from satellite.dpll import find_pure, find_unit, pure_literal_assign, unit_propagate
from satellite.expr import And, Or, var

w, x, y, z = var("w x y z")


def test_find_unit() -> None:
    expr = (w | x) & Or(y) & (y | z)
    assert find_unit(expr) == y

    expr = (w | x) & Or(~y) & (y | z)
    assert find_unit(expr) == ~y

    expr = (w | x) & (y | z)
    assert find_unit(expr) is None


def test_unit_propagate() -> None:
    expr = (w | x) & Or(y) & (y | z) & (z | ~y)
    expected = (w | x) & Or(z)
    assert unit_propagate(y, expr) == expected


def test_find_pure() -> None:
    assert find_pure((w | x) & (y | z)) == {w, x, y, z}
    assert find_pure((w | ~w) & (y | ~z)) == {y, ~z}


def test_pure_literal_assign() -> None:
    assert pure_literal_assign(y, (w | ~w) & (y | z)) == And(w | ~w)
    assert pure_literal_assign(~x, (w | ~w) & (y | z) & (w | ~x)) == (w | ~w) & (y | z)
