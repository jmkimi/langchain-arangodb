from typing import Dict, Tuple, Union
from langchain_core.structured_query import (
    Comparator,
    Comparison,
    Operation,
    Operator,
    StructuredQuery,
    Visitor,
)


class ArangoTranslator(Visitor):
    """Translate `StructuredQuery` elements to AQL filter-compatible expressions."""

    allowed_operators = [Operator.AND, Operator.OR]
    allowed_comparators = [
        Comparator.EQ,
        Comparator.NE,
        Comparator.GTE,
        Comparator.LTE,
        Comparator.LT,
        Comparator.GT,
    ]

    def _format_func(self, func: Union[Operator, Comparator]) -> str:
        self._validate_func(func)
        map_dict = {
            Operator.AND: "AND",
            Operator.OR: "OR",
            Comparator.EQ: "==",
            Comparator.NE: "!=",
            Comparator.GTE: ">=",
            Comparator.LTE: "<=",
            Comparator.LT: "<",
            Comparator.GT: ">",
        }
        return map_dict[func]

    def visit_operation(self, operation: Operation) -> str:
        args = [arg.accept(self) for arg in operation.arguments]
        operator = self._format_func(operation.operator)
        return f"({f' {operator} '.join(args)})"

    def visit_comparison(self, comparison: Comparison) -> str:
        comparator = self._format_func(comparison.comparator)
        value = comparison.value
        if isinstance(value, str):
            value = f'"{value}"'
        return f'doc.{comparison.attribute} {comparator} {value}'

    def visit_structured_query(
            self, structured_query: StructuredQuery
    ) -> Tuple[str, Dict[str, str]]:
        query = structured_query.query
        if structured_query.filter:
            filter_expr = structured_query.filter.accept(self)
            return query, {"filter": filter_expr}
        else:
            return query, {}
