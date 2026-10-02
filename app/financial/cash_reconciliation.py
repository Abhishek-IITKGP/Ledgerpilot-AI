from decimal import Decimal

from app.financial.models import CashMovementData, CashMovementDirection, CashMovementStatus


def calculate_actual_cash(
    movements: list[CashMovementData]
) -> Decimal:

    actual_cash = Decimal("0.00")

    for movement in movements:

        if movement.status != CashMovementStatus.COMPLETED:
            continue

        if movement.direction == CashMovementDirection.CREDIT:
            actual_cash += movement.amount

        elif movement.direction == CashMovementDirection.DEBIT:
            actual_cash -= movement.amount

        else:
            raise ValueError(
                f"Unsupported cash movement direction: "
                f"{movement.direction}"
            )

    return actual_cash