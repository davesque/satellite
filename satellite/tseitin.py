from typing import Dict, Iterator, List, Set

from satellite.expr import And, Connective, Equivalent, Expr, Implies, Not, Or, Var


ord_a = ord("a")


def letter_carry(places: List[int]) -> None:
    i = 0
    while True:
        if places[i] < 26:
            break

        places[i] = 0
        if len(places) == i + 1:
            places.append(0)
        else:
            places[i + 1] += 1

        i += 1


def letters() -> Iterator[str]:
    places = [0]
    while True:
        yield "".join(chr(ord_a + p) for p in reversed(places))
        places[0] += 1
        letter_carry(places)


class Tseitin:
    __slots__ = ("expr", "equivalences", "renames", "name_gen", "root")

    expr: Expr
    equivalences: Set[Equivalent]
    renames: Dict[Var, Var]
    name_gen: Iterator[str]
    root: Expr

    def __init__(self, expr: Expr) -> None:
        self.expr = expr
        self.equivalences = set()
        self.renames = {}
        self.name_gen = letters()

        self.root = self.rewrite(expr)

    def new_var(self) -> Var:
        return Var(next(self.name_gen))

    def lookup(self, orig_var: Var) -> Var:
        try:
            return self.renames[orig_var]
        except KeyError:
            new_var = self.new_var()
            self.renames[orig_var] = new_var
            return new_var

    def rewrite(self, expr: Expr) -> Expr:
        match expr:
            case Var(_):
                return self.lookup(expr)

            case Not(Var(_) as var):
                return Not(self.lookup(var))

            case Not(p):
                lhs = self.new_var()
                rhs = Not(self.rewrite(p))

            case Connective((p, q)):
                lhs = self.new_var()
                rhs = type(expr)(self.rewrite(p), self.rewrite(q))

            # special case for left-associative operators with more than 2 args
            case And((*ps, q)) | Or((*ps, q)):
                lhs = self.new_var()
                rhs = type(expr)(
                    self.rewrite(type(expr)(*ps)),
                    self.rewrite(q),
                )

            case _:
                assert False

        self.equivalences.add(Equivalent(lhs, rhs))
        return lhs

    @staticmethod
    def equiv_to_cnf(equiv: Equivalent) -> And:
        """
        Convert an equivalence to a CNF clause.

        Each of these match cases should work regardless of the polarity of
        right-hand side literals.
        """
        match equiv:
            case Equivalent((p, Not(q))):
                # p <-> ~q
                # = (p -> ~q) & (~q -> p)
                # = (~p | ~q) & (q | p)
                return (~p | ~q) & (q | p)

            case Equivalent((p, Implies((q, r)))):
                # p <-> (q -> r)
                # = (~p | (q -> r)) & (~(q -> r) | p)
                # = (~p | (~q | r)) & (~(~q | r) | p)
                # = (~p | ~q | r) & (q & ~r | p)
                # = (~p | ~q | r) & (q | p) & (~r | p)
                return (~p | ~q | r) & (q | p) & (~r | p)

            case Equivalent((p, Or((q, r)))):
                # p <-> (q | r)
                # = (~p | (q | r)) & (~(q | r) | p)
                # = (~p | q | r) & (~q & ~r | p)
                # = (~p | q | r) & (~q | p) & (~r | p)
                return (~p | q | r) & (~q | p) & (~r | p)

            case Equivalent((p, And((q, r)))):
                # p <-> (q & r)
                # = (~p | (q & r)) & (~(q & r) | p)
                # = (~p | q) & (~p | r) & (~q | ~r | p)
                return (~p | q) & (~p | r) & (~q | ~r | p)

        assert False

    def transform(self) -> And:
        parts: List[Expr] = [Or(self.root)]
        for equiv in self.equivalences:
            and_expr = self.equiv_to_cnf(equiv)
            parts.extend(and_expr.args)

        return And(*parts)
