"""Business document generation (BACKLOG.md 2.7, DATASET.md §19-24).

Each document is authored as Markdown (one of the formats CLAUDE.md §3 / Phase 3
will support) and additionally rendered to PDF, since DATASET.md §19 names the
five documents with a `.pdf` extension and Phase 3 needs real PDF fixtures to
build/test its parser against. The Markdown source stays alongside the PDF as
the readable source of truth.

Content is written by hand (not templated from ground truth): DATASET.md §23
explicitly requires the migration report to *not* state that the migration
caused the refund increase, and the refund/shipping policies must not contain
the hidden causal conclusion at all - only the incident report may hint at it,
and even that stays observational rather than conclusory.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    filename_stem: str
    title: str
    sections: list[tuple[str, str]]  # (heading, body)


REFUND_POLICY = Document(
    filename_stem="Refund Policy",
    title="Northstar Commerce - Refund Policy",
    sections=[
        (
            "Eligibility",
            "Customers may request a refund within 30 days of the delivery date for most items, "
            "provided the product is unused or defective. Digital gift cards and final-sale "
            "clearance items are not eligible for refund.",
        ),
        (
            "Refund Window",
            "Standard refund requests must be submitted within 30 days of delivery. Requests "
            "related to a delayed or non-arrived shipment may be submitted at any point after "
            "the estimated delivery window has passed, without waiting for the item to arrive.",
        ),
        (
            "Delivery-Delay Handling",
            "If an order has not arrived within a reasonable time after the estimated delivery "
            "window, the customer may request either a replacement shipment or a full refund. "
            "Support agents should confirm the current shipment status before approving a "
            "delay-related refund, and should reference the Shipping Policy for the standard "
            "delivery window when evaluating these requests.",
        ),
        (
            "Approval Rules",
            "Refunds for damaged or defective products require photo evidence where practical. "
            "Refunds tied to shipping delays do not require photo evidence, since the product "
            "itself may not have been received. Billing-related refund requests are routed to "
            "the billing team and are not handled under this policy.",
        ),
        (
            "Processing Time",
            "Approved refunds are typically processed within 1-4 business days of approval. "
            "Refunded amounts are returned to the original payment method.",
        ),
    ],
)

SHIPPING_POLICY = Document(
    filename_stem="Shipping Policy",
    title="Northstar Commerce - Shipping Policy",
    sections=[
        (
            "Standard Delivery Window",
            "Northstar Commerce targets a standard delivery window of 2-4 business days from the "
            "time an order ships. This window applies to standard domestic shipments under normal "
            "operating conditions.",
        ),
        (
            "Shipping Providers",
            "Orders are fulfilled through one or more contracted shipping providers. Northstar "
            "Commerce selects providers based on cost, coverage, and reliability, and may adjust "
            "provider allocation over time as part of normal operations.",
        ),
        (
            "Delayed-Order Procedure",
            "An order is considered delayed once it exceeds the standard delivery window without "
            "being marked delivered. Delayed orders should be flagged for proactive customer "
            "communication where possible, and are eligible for the delivery-delay handling "
            "described in the Refund Policy.",
        ),
        (
            "Provider Responsibilities",
            "Shipping providers are responsible for timely pickup, transit, and delivery "
            "confirmation. Northstar Commerce monitors aggregate delivery performance by provider "
            "and reviews providers whose performance falls outside expected ranges.",
        ),
    ],
)

CUSTOMER_SUPPORT_HANDBOOK = Document(
    filename_stem="Customer Support Handbook",
    title="Northstar Commerce - Customer Support Handbook",
    sections=[
        (
            "Escalation Rules",
            "Tickets marked 'urgent' priority, or from customers in the 'high_value' segment, "
            "should be escalated to a senior support agent within one business day. Tickets "
            "involving repeated contact about the same order should also be escalated rather "
            "than closed as duplicates.",
        ),
        (
            "Delayed-Shipment Procedure",
            "When a customer contacts support about a delayed shipment, agents should check the "
            "current tracking status, confirm whether the order has exceeded the standard "
            "delivery window in the Shipping Policy, and offer either continued tracking, a "
            "replacement, or a refund per the Refund Policy's delivery-delay handling section.",
        ),
        (
            "Refund Escalation",
            "Refund requests that fall outside standard policy (for example, requests past the "
            "30-day window without a delivery delay involved) should be escalated to a support "
            "lead rather than approved or denied directly by a front-line agent.",
        ),
        (
            "High-Value Customer Handling",
            "Customers in the 'high_value' segment should receive proactive updates on any "
            "known delivery issues affecting their order, rather than waiting for the customer "
            "to reach out first, where the support team has visibility into the issue.",
        ),
    ],
)

SHIPPING_PROVIDER_MIGRATION_REPORT = Document(
    filename_stem="Shipping Provider Migration Report",
    title="Northstar Commerce - Shipping Provider Migration Report",
    sections=[
        (
            "Summary",
            "Effective July 11, Northstar Commerce began routing a substantial share of order "
            "fulfillment from SwiftShip to a new shipping partner, RapidShip Logistics. This "
            "report documents the migration timeline and business rationale.",
        ),
        (
            "Previous Provider",
            "SwiftShip has been Northstar Commerce's primary shipping provider and continues to "
            "handle a portion of order volume following the migration.",
        ),
        (
            "New Provider",
            "RapidShip Logistics was selected following a vendor evaluation process focused on "
            "fulfillment cost. RapidShip began handling a majority share of new orders starting "
            "July 11.",
        ),
        (
            "Business Motivation",
            "The primary motivation for the migration was cost reduction. RapidShip's proposed "
            "rate structure was expected to reduce Northstar Commerce's overall shipping cost by "
            "approximately 12% at current order volumes.",
        ),
        (
            "Expected Benefit",
            "Beyond direct cost savings, RapidShip's contract included expanded regional coverage "
            "that SwiftShip did not offer. The migration was approved on the basis of these "
            "combined cost and coverage benefits.",
        ),
    ],
)

JULY_OPERATIONS_INCIDENT_REPORT = Document(
    filename_stem="July Operations Incident Report",
    title="Northstar Commerce - July Operations Incident Report",
    sections=[
        (
            "Overview",
            "This report summarizes operational observations from the Operations team during "
            "July, following the onboarding of a new shipping partner earlier in the month.",
        ),
        (
            "Tracking Delays",
            "Several warehouse and logistics staff reported that tracking updates for shipments "
            "handled by the new shipping partner were arriving later and less consistently than "
            "expected during the first weeks after onboarding.",
        ),
        (
            "Warehouse Handoff Issues",
            "The warehouse team noted intermittent delays during the handoff of packages to the "
            "new shipping partner's pickup process, particularly during the initial ramp-up "
            "period, which the team attributed to unfamiliarity with the new pickup schedule.",
        ),
        (
            "Customer Escalations",
            "Support leadership noted an increase in customer escalations referencing delivery "
            "timing during the same period. This report does not attempt to quantify the increase; "
            "see the analytics dashboard for measured ticket and refund trends.",
        ),
        (
            "Monitoring Notes",
            "Operations is continuing to monitor delivery performance by shipping provider on an "
            "ongoing basis and will report further findings as more data becomes available.",
        ),
    ],
)

ALL_DOCUMENTS: list[Document] = [
    REFUND_POLICY,
    SHIPPING_POLICY,
    CUSTOMER_SUPPORT_HANDBOOK,
    SHIPPING_PROVIDER_MIGRATION_REPORT,
    JULY_OPERATIONS_INCIDENT_REPORT,
]


def render_markdown(document: Document) -> str:
    lines = [f"# {document.title}", ""]
    for heading, body in document.sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


def write_document_markdown(document: Document, output_dir: Path) -> Path:
    from northstar.writer import write_text

    path = output_dir / f"{document.filename_stem}.md"
    write_text(path, render_markdown(document))
    return path


def write_document_pdf(document: Document, output_dir: Path) -> Path:
    from fpdf import FPDF

    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, document.title)
    pdf.ln(4)

    for heading, body in document.sections:
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, heading)
        pdf.ln(1)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, body)
        pdf.ln(4)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{document.filename_stem}.pdf"
    pdf.output(str(path))
    return path


def write_all_documents(output_dir: Path) -> list[Path]:
    paths = []
    for document in ALL_DOCUMENTS:
        paths.append(write_document_markdown(document, output_dir))
        paths.append(write_document_pdf(document, output_dir))
    return paths
