from enum import StrEnum


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_class]


class UserRole(StrEnum):
    EMPLOYEE = "employee"
    ADMIN = "admin"


class WorkSessionStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    LOCKED = "locked"


class BreakType(StrEnum):
    MEAL = "meal"
    REST = "rest"
    OTHER = "other"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OffDayType(StrEnum):
    PERSONAL = "personal"
    COMPANY = "company"
    HOLIDAY = "holiday"
    SICK = "sick"
    OTHER = "other"


class TimesheetStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RETURNED = "returned"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAYABLE = "payable"
    PAID = "paid"


class ApprovalDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAYABLE = "payable"
    PAID = "paid"
    CANCELLED = "cancelled"


class InvoiceStatus(StrEnum):
    GENERATED = "generated"
    ISSUED = "issued"
    CANCELLED = "cancelled"
