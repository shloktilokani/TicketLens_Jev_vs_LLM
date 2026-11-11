"""Task definitions given identically to both providers (ai-evaluation.md section 3), so the
comparison is fair: same categories, same priority, sentiment and escalation meanings."""

from app.core.taxonomy import active_categories

PRIORITY = {
    "Critical": "Immediate risk, safety/security concern, severe service failure, or high-impact "
    "account/payment issue requiring urgent human attention.",
    "High": "Major customer impact, significant delay, failed essential transaction, or repeated "
    "unresolved issue.",
    "Medium": "Normal issue requiring support but without immediate severe impact.",
    "Low": "Informational request, minor inconvenience, or non-urgent feedback.",
}
SENTIMENT = {
    "Positive": "Appreciation, satisfaction, or clearly favorable tone.",
    "Neutral": "Factual/informational language without clear positive or negative emotion.",
    "Negative": "Frustration, dissatisfaction, anger, disappointment, or distress.",
}
ESCALATION = (
    "Escalate when the issue involves safety, suspected fraud, account compromise, legal "
    "threats, sensitive personal data exposure, repeated unresolved severe issues, or a "
    "critical/high-impact situation requiring a human specialist. Do not escalate merely "
    "because a ticket is negative."
)


def category_criteria() -> dict[str, str]:
    return {c: "Covers: " + ", ".join(subs) + "." for c, subs in active_categories().items()}


def subcategory_criteria() -> dict[str, str]:
    return {sub: f"Part of {c}." for c, subs in active_categories().items() for sub in subs}


INSTRUCTIONS = (
    "You classify customer-support tickets for ShopKart, an Indian e-commerce marketplace. "
    "Classify only from the ticket's own evidence; do not invent order facts or company policy. "
    "Choose the closest allowed category and a subcategory that belongs to it."
)
