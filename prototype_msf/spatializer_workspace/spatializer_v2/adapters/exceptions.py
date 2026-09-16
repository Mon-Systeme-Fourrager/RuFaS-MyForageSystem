"""
Exceptions for RUFAS → Evaluator adapters.
"""


class IncompleteRufasStateError(Exception):
    """Raised when RUFAS state lacks data required by an evaluator.

    Attributes
    ----------
    missing_fields : list[str]
        Names of the RUFAS attributes that were not found or None.
    field_id : str
        The RUFAS field being adapted.
    """

    def __init__(self, missing_fields: list[str], field_id: str) -> None:
        self.missing_fields = missing_fields
        self.field_id = field_id
        super().__init__(
            f"Cannot build inputs for field '{field_id}': "
            f"missing/None fields = {missing_fields}"
        )
