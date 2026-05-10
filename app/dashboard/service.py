from collections import Counter

from app.audits.models import Audit
from app.dashboard.schemas import DashboardStatistics, DenialReason, LatestAuditItem
from app.shared.enums import CaseStatus


async def get_dashboard_statistics() -> DashboardStatistics:
    audits = await Audit.find_all().sort("-created_at").to_list()
    latest_by_case = {}
    for audit in audits:
        latest_by_case.setdefault(str(audit.case_id), audit)

    latest_cases = list(latest_by_case.values())
    total = len(latest_cases)
    approved = sum(1 for item in latest_cases if item.status == CaseStatus.APROBADO)
    observed = sum(1 for item in latest_cases if item.status == CaseStatus.OBSERVADO)
    denied = sum(1 for item in latest_cases if item.status == CaseStatus.DENEGADO)
    human_review = sum(1 for item in latest_cases if item.status == CaseStatus.REVISION_HUMANA)
    approval_rate = round((approved / total) * 100) if total else 0

    return DashboardStatistics(
        total_cases=total,
        approved_cases=approved,
        observed_cases=observed,
        denied_cases=denied,
        human_review_cases=human_review,
        approval_rate=approval_rate,
        latest_audits=[
            LatestAuditItem(
                audit_id=item.audit_id,
                case_id=item.case_claim_number,
                status=item.status.value,
                created_at=item.created_at,
            )
            for item in audits[:5]
        ],
    )


async def get_denial_reasons() -> list[DenialReason]:
    denied_audits = await Audit.find(Audit.status == CaseStatus.DENEGADO).to_list()
    counter: Counter[str] = Counter()
    for audit in denied_audits:
        for discrepancy in audit.discrepancies:
            reason = discrepancy.get("message") or discrepancy.get("type") or "Dato no disponible"
            counter[reason] += 1

    total = sum(counter.values())
    if total == 0:
        return []

    return [
        DenialReason(reason=reason, count=count, percentage=round((count / total) * 100))
        for reason, count in counter.most_common(5)
    ]
