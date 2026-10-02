from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class ReconciliationDirection(Enum):
    MATCH = "MATCH"
    SHORTFALL = "SHORTFALL"
    EXECESS = "EXCESS"

class ReconciliationStatus(Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"

class CashMovementDirection(Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class CashMovementStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class InvestigationStatus(Enum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'
  

@dataclass
class ReconciliationResult: 
    status: ReconciliationStatus
    expected_cash: Decimal
    actual_cash: Decimal
    difference: Decimal
    absolute_difference: Decimal
    reconciliation_direction: ReconciliationDirection

@dataclass
class SettlementCashData:
    settlement_id : int
    expected_cash : Decimal
    actual_cash : Decimal

@dataclass
class CashMovementData:
    cash_movement_id: int
    settlement_id: int
    account_id: int
    movement_type: str
    direction: CashMovementDirection
    amount: Decimal
    currency: str
    status: str




