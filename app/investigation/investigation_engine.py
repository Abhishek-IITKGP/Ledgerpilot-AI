from app.investigation.models import InvestigationFinding
from app.financial.models import CashMovementData, CashMovementDirection


class InvestigationEngine:

    def investigate(self, context):

        settlement = context.settlement
        transaction = context.transaction

        evidence = []
        root_causes = []

        completed_executions = [
            execution
            for execution in context.executions
            if execution.status == "COMPLETED"
        ]

        for execution in completed_executions:
            execution_value = (
                execution.execution_quantity
                * execution.execution_price
            )

            evidence.append(
                f"Execution completed: "
                f"{execution.execution_quantity} shares @ "
                f"{execution.execution_price}"
            )

            evidence.append(
                f"Execution value: {execution_value}"
            )

        if transaction.net_amount == settlement.expected_cash:
            evidence.append(
                "Transaction net amount matches expected settlement cash"
            )

        if settlement.status == "FAILED":
            root_causes.append("INVALID_SETTLEMENT_INSTRUCTION")
            evidence.append(
                f"Settlement failed: {settlement.failure_reason}"
            )

        if transaction.status == "COMPLETED":
            evidence.append(
                "Transaction completed successfully"
            )

        completed_cash_movements = [
            movement
            for movement in context.cash_movements
            if movement.status == "COMPLETED"
        ]

        actual_cash_from_movements = sum(
            movement.amount
            if movement.direction == CashMovementDirection.CREDIT
            else -movement.amount
            for movement in completed_cash_movements
        )

        if not completed_cash_movements:
            evidence.append(
                "No completed cash movement was recorded"
            )

        if actual_cash_from_movements != settlement.expected_cash:
            root_causes.append("CASH_MOVEMENT_MISMATCH")
            evidence.append(
                f"Cash movement total ({actual_cash_from_movements}) "
                f"does not match expected settlement cash "
                f"({settlement.expected_cash})"
            )
        else:
            evidence.append(
                "Cash movement total matches expected settlement cash"
            )       

        execution_total = self._calculate_execution_total(context)

        execution_transaction_difference = abs(
            execution_total - transaction.gross_amount
        )

        if execution_total != transaction.gross_amount:
            root_causes.append("EXECUTION_TRANSACTION_MISMATCH")
            evidence.append(
                f"Execution total ({execution_total}) does not match "
                f"transaction gross amount ({transaction.gross_amount})"
            )

        execution_quantity = sum(
            execution.execution_quantity
            for execution in completed_executions
        )

        if execution_quantity != context.order.quantity:
            root_causes.append("ORDER_EXECUTION_MISMATCH")
            evidence.append(
                f"Execution quantity ({execution_quantity}) does not match "
                f"order quantity ({context.order.quantity})"
        )
        
        impact = context.case.discrepancy

        if not root_causes:
            root_causes.append("UNKNOWN")

        severity = self._determine_severity(impact)

        return InvestigationFinding(
            root_causes=root_causes,
            impact=impact,
            severity=severity,
            evidence=evidence,
            recommended_action=self._recommend_action(root_causes),
        )

    def _determine_severity(self, impact):
        if impact == 0:
            return "LOW"

        if impact < 1000:
            return "MEDIUM"

        return "HIGH"

    def _recommend_action(self, root_causes):

        if (
            "INVALID_SETTLEMENT_INSTRUCTION" in root_causes
            and "CASH_MOVEMENT_MISMATCH" in root_causes
        ):
            return (
                "Review the settlement instruction and investigate the "
                "cash movement discrepancy before reprocessing settlement."
        )

        if "ORDER_EXECUTION_MISMATCH" in root_causes:
            return (
                "Review the order and execution quantities "
                "and investigate the execution discrepancy."
            )

        if "EXECUTION_TRANSACTION_MISMATCH" in root_causes:
            return (
                "Review execution values and transaction amount, "
                "then correct the transaction before reprocessing settlement."
            )

        if "CASH_MOVEMENT_MISMATCH" in root_causes:
                    return (
                        "Investigate the recorded cash movement and reconcile "
                        "it with the expected settlement amount."
                    )

        if "INVALID_SETTLEMENT_INSTRUCTION" in root_causes:
            return (
                "Review and correct the settlement instruction, "
                "then reprocess settlement."
            )

        return (
            "Review settlement failure and investigate "
            "the underlying cause."
        )

    def _calculate_execution_total(self, context):
        return sum(
            execution.execution_quantity * execution.execution_price
            for execution in context.executions
            if execution.status == "COMPLETED"
        )
