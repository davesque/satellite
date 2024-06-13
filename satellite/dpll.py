from collections import defaultdict
import logging
import random
from typing import Callable

from satellite.expr import And, CNF, Connective, Expr, Lit, Not, Or, Var

logger = logging.getLogger(__name__)


type ChooseLit = Callable[[CNF], Lit]


def count_lits(expr: Expr, counter: dict[Var, int]) -> None:
    match expr:
        case Var(_):
            # if name.startswith("x"):
            counter[expr] += 1
        case Not(p):
            count_lits(p, counter)
        case Connective(args):
            for arg in args:
                count_lits(arg, counter)


def common_lit(expr: CNF) -> Lit:
    counter = defaultdict(lambda: 0)
    count_lits(expr, counter)

    counts = sorted(counter.items(), key=lambda i: i[1], reverse=True)
    return counts[0][0]


def first_lit(expr: CNF) -> Lit:
    or_expr = expr.args[0]
    return or_expr.args[0]


def last_lit(expr: CNF) -> Lit:
    or_expr = expr.args[-1]
    return or_expr.args[-1]


def random_lit(expr: CNF) -> Lit:
    or_expr = random.choice(expr.args)
    lit = random.choice(or_expr.args)
    return lit


class DPLL:
    __slots__ = ("expr", "choose_lit")

    expr: CNF
    choose_lit: ChooseLit

    def __init__(self, expr: CNF, choose_lit: ChooseLit = common_lit) -> None:
        self.expr = expr
        self.choose_lit = choose_lit

    def check(self, expr: CNF | None = None) -> bool:
        """
        The Davis-Putnam-Logemann-Loveland (DPLL) SAT algorithm.

        Implementation based on the following description:
        https://en.wikipedia.org/wiki/DPLL_algorithm
        """
        if expr is None:
            expr = self.expr

        while lit := self.find_unit(expr):
            expr = self.unit_propagate(lit, expr)

        while pure_lits := self.find_pure(expr):
            for lit in pure_lits:
                expr = self.pure_literal_assign(lit, expr)

        # If the root conjunction is empty, this implies that the formula is
        # satisfiable.  This follows from the fact that any clause that was
        # eliminated from the root conjunction was determined to have a truth value
        # of `true`. Therefore, the root conjunction also evaluates to true.
        if len(expr.args) == 0:
            return True

        # If any disjunctive clause is empty, this implies that the formula is not
        # satisfiable.  This follows from the fact that any literal that was
        # eliminated from a disjunction was determined to have a truth value of
        # `false`.  Therefore, the parent disjunction evaluates to `false` and the
        # root conjunction also evaluate to `false`.
        for or_expr in expr.args:
            if len(or_expr.args) == 0:
                return False

        lit = self.choose_lit(expr)

        logger.debug("+++++++++++++ branching +++++++++++++")
        if self.check(self.unit_propagate(lit, expr)):
            return True
        logger.debug("------------ backtracking -----------")
        return self.check(self.unit_propagate(~lit, expr))

    @staticmethod
    def find_unit(and_expr: CNF) -> Expr | None:
        for or_expr in and_expr.args:
            if len(or_expr.args) == 1:
                return or_expr.args[0]

    @staticmethod
    def unit_propagate(lit: Expr, and_expr: CNF) -> CNF:
        logger.debug("eliminating unit: %s", lit)

        not_lit = ~lit
        and_args = []
        for or_expr in and_expr.args:
            delete = False
            or_args = []
            for or_lit in or_expr.args:
                # delete any disjunction that contains the literal
                if or_lit == lit:
                    delete = True
                    break

                # delete any arg equal to the literal's negation
                if or_lit == not_lit:
                    continue

                or_args.append(or_lit)

            if not delete:
                and_args.append(Or(*or_args))

        return And(*and_args)

    @staticmethod
    def find_pure(and_expr: CNF) -> set[Expr]:
        lit_variants = defaultdict(set)
        for or_expr in and_expr.args:
            for or_lit in or_expr.args:
                atom = or_lit.atom()
                lit_variants[atom].add(or_lit)

        pure_lits = {tuple(v)[0] for v in lit_variants.values() if len(v) == 1}
        return pure_lits

    @staticmethod
    def pure_literal_assign(lit: Expr, and_expr: CNF) -> CNF:
        logger.debug("eliminating pure literal: %s", lit)

        and_args = []
        for or_expr in and_expr.args:
            if lit not in or_expr.args:
                and_args.append(or_expr)

        return And(*and_args)
