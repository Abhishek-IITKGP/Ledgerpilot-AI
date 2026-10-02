from app.application import create_investigation_workflow
from app.database.connection import get_connection


def main():
    settlement_id = int(input("Enter settlement ID: "))

    with get_connection() as connection:
        workflow = create_investigation_workflow(connection)

        finding = workflow.investigate_settlement(settlement_id)

        if finding is None:
            print("No discrepancy found.")
            return

        print()
        print("=== FinSight Investigation ===")
        print()

        print("Root Causes:")
        for root_cause in finding.root_causes:
            print(f"- {root_cause}")

        print(f"Impact: {finding.impact}")
        print(f"Severity: {finding.severity}")
        print()

        print("Evidence:")
        for item in finding.evidence:
            print(f"- {item}")

        print()
        print(
            f"Recommended Action: {finding.recommended_action}"
        )


if __name__ == "__main__":
    main()