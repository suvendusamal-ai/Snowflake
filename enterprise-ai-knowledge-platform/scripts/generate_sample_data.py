#!/usr/bin/env python3
"""Generate realistic sample documents for all 9 departments.

Creates text-based sample documents that exercise the full pipeline:
ingestion → parsing → classification → chunking → embedding → search.

Usage:
    python scripts/generate_sample_data.py [--output-dir data/sample_documents]
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "sample_documents"

# ─── Sample Document Content per Department ──────────────────────────────────

DOCUMENTS: dict[str, list[dict[str, str]]] = {
    "finance": [
        {
            "filename": "Q4_2024_Financial_Report.txt",
            "content": """QUARTERLY FINANCIAL REPORT - Q4 2024

EXECUTIVE SUMMARY
Total revenue for Q4 2024 reached $2.87 billion, representing a 12.3% year-over-year increase.
Operating margin improved to 23.4%, up from 21.1% in Q4 2023. Net income attributable to
shareholders was $485 million, or $3.42 per diluted share.

REVENUE BREAKDOWN BY SEGMENT
- Enterprise Solutions: $1.42B (+15.2% YoY)
- Cloud Services: $890M (+18.7% YoY)
- Professional Services: $560M (+4.1% YoY)

OPERATING EXPENSES
Total operating expenses were $2.19B, representing 76.6% of revenue.
- Cost of Revenue: $1.21B (42.2% of revenue)
- Research & Development: $412M (14.4% of revenue)
- Sales & Marketing: $387M (13.5% of revenue)
- General & Administrative: $184M (6.4% of revenue)

CASH FLOW
Operating cash flow was $612M. Free cash flow reached $487M after capital expenditures
of $125M. The company returned $200M to shareholders through dividends and $150M through
share repurchases.

OUTLOOK FOR Q1 2025
Management expects revenue in the range of $2.95B to $3.05B, with operating margin
between 23.0% and 24.0%. Capital expenditure is expected to increase to $150M to support
cloud infrastructure expansion.

Prepared by: Finance Division
Fiscal Year: 2024
Cost Center: CC-1000
Approval Status: Approved by CFO
""",
        },
        {
            "filename": "Annual_Budget_FY2025.txt",
            "content": """ANNUAL BUDGET PLAN - FISCAL YEAR 2025

BUDGET OVERVIEW
Total planned expenditure: $9.2 billion
Revenue target: $12.5 billion
Planned operating margin: 24.0%

DEPARTMENT ALLOCATIONS
1. Engineering & Product: $2.8B (30.4% of budget)
2. Sales & Marketing: $2.1B (22.8% of budget)
3. Operations: $1.6B (17.4% of budget)
4. General & Administrative: $0.9B (9.8% of budget)
5. Research & Development: $1.8B (19.6% of budget)

KEY INVESTMENTS
- AI/ML Infrastructure: $450M (new initiative)
- Data Center Expansion: $320M (Asia-Pacific region)
- Talent Acquisition: $180M (2,500 new hires planned)
- Security & Compliance: $95M (+25% vs FY2024)

BUDGET GOVERNANCE
- Monthly variance reviews with department heads
- Quarterly reforecasting cycles
- 5% contingency reserve ($460M) for unplanned needs
- All expenditures over $5M require CFO approval

Account Code: BUDGET-2025-MASTER
Approval Authority: Board of Directors
Review Cycle: Quarterly
""",
        },
    ],
    "treasury": [
        {
            "filename": "Cash_Management_Policy_2024.txt",
            "content": """CORPORATE CASH MANAGEMENT POLICY

EFFECTIVE DATE: January 1, 2024
POLICY OWNER: Treasury Department
REVIEW FREQUENCY: Annual

1. LIQUIDITY REQUIREMENTS
- Minimum cash reserve: $500M across all accounts
- Maximum single-bank concentration: 25% of total cash
- Operating cash buffer: 3 months of operating expenses

2. INVESTMENT POLICY
Permitted instruments:
- US Treasury Securities (no maturity limit)
- Investment-grade corporate bonds (max 5-year maturity)
- Money market funds (SEC-registered only)
- Commercial paper (A-1/P-1 rated, max 90-day maturity)

Prohibited investments:
- Equities or equity derivatives
- Structured products
- Below investment-grade securities
- Cryptocurrency or digital assets

3. FOREIGN EXCHANGE MANAGEMENT
- Natural hedging preferred for predictable flows
- Forward contracts permitted for exposures > $10M
- Options permitted with CFO pre-approval
- Maximum hedge tenor: 12 months
- Counterparty credit rating minimum: A-

4. BANKING RELATIONSHIPS
Primary banks: JP Morgan, Bank of America, Citigroup
Secondary banks: Wells Fargo, HSBC
All banks must maintain minimum rating of A+.

Instrument Type: Policy Document
Currency: Multi-currency (USD primary)
Interest Rate: Variable based on instrument
Counterparty: Multiple
""",
        },
    ],
    "procurement": [
        {
            "filename": "Vendor_Contract_Template_2024.txt",
            "content": """MASTER SERVICE AGREEMENT - TEMPLATE

CONTRACT REFERENCE: MSA-2024-TEMPLATE
VERSION: 3.2
EFFECTIVE DATE: [Date]

PARTIES:
- Buyer: [Company Name] ("Company")
- Vendor: [Vendor Name] ("Supplier")

1. SCOPE OF SERVICES
The Supplier shall provide the services described in Exhibit A attached hereto,
in accordance with the service levels defined in Exhibit B.

2. TERM AND TERMINATION
- Initial term: 36 months from Effective Date
- Auto-renewal: 12-month periods unless terminated with 90 days notice
- Termination for cause: 30 days written notice with cure period
- Termination for convenience: 60 days written notice

3. PRICING AND PAYMENT
- Pricing per Exhibit C (Rate Card)
- Payment terms: Net 45 from invoice date
- Annual price increase cap: CPI + 2%
- Volume discounts per Exhibit C

4. SERVICE LEVEL AGREEMENTS
- System availability: 99.95% monthly
- Response time (P1): 15 minutes
- Resolution time (P1): 4 hours
- Service credits: 2% per 0.01% below target

5. DATA PROTECTION
- Supplier shall comply with Company's Data Protection Policy
- Annual SOC 2 Type II report required
- Right to audit with 30 days notice
- Data residency: United States and EU only

6. INSURANCE REQUIREMENTS
- General liability: $5M per occurrence
- Professional liability: $10M aggregate
- Cyber liability: $5M per occurrence

Vendor Name: [Template]
Contract Value: [Variable]
Contract Start Date: [Date]
Contract End Date: [Date + 36 months]
Payment Terms: Net 45
Category: Professional Services
""",
        },
    ],
    "risk": [
        {
            "filename": "Enterprise_Risk_Register_Q4_2024.txt",
            "content": """ENTERPRISE RISK REGISTER - Q4 2024

RISK ID: ERM-001
CATEGORY: Operational
RISK: Major data center outage affecting multiple regions
LIKELIHOOD: Medium (3/5)
IMPACT: High (4/5)
RISK SCORE: 12/25
MITIGATION: Multi-region failover, 99.99% SLA with providers
RISK OWNER: VP Infrastructure
ASSESSMENT DATE: December 15, 2024
STATUS: Monitored - controls in place

---

RISK ID: ERM-002
CATEGORY: Cybersecurity
RISK: Ransomware attack on critical systems
LIKELIHOOD: Medium-High (3.5/5)
IMPACT: Critical (5/5)
RISK SCORE: 17.5/25
MITIGATION: Zero-trust architecture, 24/7 SOC, immutable backups, tabletop exercises quarterly
RISK OWNER: CISO
ASSESSMENT DATE: December 15, 2024
STATUS: Active mitigation - enhanced monitoring deployed

---

RISK ID: ERM-003
CATEGORY: Regulatory
RISK: Non-compliance with emerging AI regulations (EU AI Act)
LIKELIHOOD: Medium (3/5)
IMPACT: High (4/5)
RISK SCORE: 12/25
MITIGATION: AI governance framework, legal review of all AI deployments, model risk management
RISK OWNER: Chief Legal Officer
ASSESSMENT DATE: December 15, 2024
STATUS: Active - governance framework under development

---

RISK ID: ERM-004
CATEGORY: Financial
RISK: FX exposure from international revenue (EUR, GBP, JPY)
LIKELIHOOD: High (4/5)
IMPACT: Medium (3/5)
RISK SCORE: 12/25
MITIGATION: Natural hedging + forward contracts for exposures > $10M
RISK OWNER: Treasurer
ASSESSMENT DATE: December 15, 2024
STATUS: Controlled - hedging program active

Risk Category: Enterprise
Likelihood: Variable
Impact Level: Variable
Mitigation Status: Active
Risk Owner: Multiple
Assessment Date: 2024-12-15
""",
        },
    ],
    "compliance": [
        {
            "filename": "SOX_Compliance_Report_2024.txt",
            "content": """SARBANES-OXLEY COMPLIANCE REPORT - FISCAL YEAR 2024

REPORT DATE: March 15, 2025
PREPARED BY: Internal Controls & Compliance Team
REVIEWED BY: External Auditor (Deloitte)

EXECUTIVE SUMMARY
The company maintained effective internal controls over financial reporting (ICFR)
throughout fiscal year 2024. No material weaknesses were identified. Two significant
deficiencies were noted and remediated during the year.

CONTROL ENVIRONMENT ASSESSMENT
Total controls tested: 342
Controls operating effectively: 337 (98.5%)
Deficiencies identified: 5
- Material weaknesses: 0
- Significant deficiencies: 2 (both remediated)
- Control deficiencies: 3 (accepted risk)

KEY FINDINGS

Finding 1: Access Review Timeliness (Significant Deficiency - REMEDIATED)
- Quarterly access reviews for financial systems completed late in Q2
- Root cause: Manual review process overwhelmed by headcount growth
- Remediation: Automated access certification tool deployed in Q3
- Status: Verified remediated in Q4 testing

Finding 2: Journal Entry Approval (Significant Deficiency - REMEDIATED)
- 3% of journal entries over $1M lacked secondary approval in Q1
- Root cause: System configuration gap after ERP upgrade
- Remediation: Approval workflow reconfigured with hard stop
- Status: Verified remediated in Q2 testing

MANAGEMENT ASSERTION
Management asserts that internal controls over financial reporting were effective
as of December 31, 2024.

Regulation: SOX Section 404
Compliance Status: Compliant
Review Date: 2025-03-15
Next Review Date: 2026-03-15
Responsible Officer: Chief Compliance Officer
Finding Count: 5
""",
        },
    ],
    "audit": [
        {
            "filename": "Internal_Audit_IT_Security_2024.txt",
            "content": """INTERNAL AUDIT REPORT
SUBJECT: IT Security Controls Assessment
AUDIT PERIOD: July 1, 2024 - December 31, 2024
REPORT DATE: February 10, 2025

AUDIT OPINION: Satisfactory with Observations

SCOPE
This audit assessed the effectiveness of IT security controls across:
- Network security and segmentation
- Identity and access management (IAM)
- Vulnerability management
- Incident response capabilities
- Third-party security governance

KEY FINDINGS

FINDING 1 (Medium Risk): Privileged Account Management
Observation: 12% of privileged accounts lack multi-factor authentication.
Impact: Increased risk of unauthorized access to critical systems.
Recommendation: Enforce MFA for all privileged accounts within 30 days.
Management Response: Accepted. MFA enrollment campaign initiated.
Target Date: March 31, 2025

FINDING 2 (Low Risk): Patch Management SLA
Observation: Critical patches applied within 15 days on average (SLA: 7 days).
Impact: Extended window of vulnerability exposure.
Recommendation: Implement automated patching for standard configurations.
Management Response: Accepted. Automation project approved.
Target Date: June 30, 2025

FINDING 3 (Medium Risk): Third-Party Security Assessment
Observation: 4 of 23 critical vendors lack current SOC 2 reports.
Impact: Unverified security controls at key suppliers.
Recommendation: Suspend data sharing until reports are obtained.
Management Response: Partially accepted. Obtaining reports by April 2025.
Target Date: April 30, 2025

TOTAL RECOMMENDATIONS: 8
HIGH RISK: 0
MEDIUM RISK: 5
LOW RISK: 3

Audit Type: IT Security
Audit Period: H2 2024
Finding Severity: Medium
Recommendation Count: 8
Auditee: IT Department
Audit Opinion: Satisfactory with Observations
""",
        },
    ],
    "hr": [
        {
            "filename": "Employee_Benefits_Policy_2025.txt",
            "content": """EMPLOYEE BENEFITS POLICY - EFFECTIVE JANUARY 1, 2025

POLICY OWNER: Human Resources Department
APPLIES TO: All full-time employees (US-based)
LAST UPDATED: December 1, 2024

1. HEALTH INSURANCE
- Medical: PPO and HDHP options (employer covers 80% of premium)
- Dental: Preventive 100%, Basic 80%, Major 50%
- Vision: Annual exam covered, $200 frame allowance
- Mental health: 30 sessions per year at $20 copay
- Family coverage available (employee + 20% premium share)

2. RETIREMENT BENEFITS
- 401(k) with 6% employer match (immediate vesting)
- Company contribution: additional 3% regardless of employee contribution
- Roth 401(k) option available
- Auto-enrollment at 6% for new hires (opt-out available)

3. PAID TIME OFF
- Vacation: 20 days (years 1-5), 25 days (years 5-10), 30 days (10+)
- Sick leave: 10 days per year (unlimited carryover)
- Personal days: 3 per year
- Parental leave: 16 weeks paid (birth/adoption, all parents)
- Bereavement: 5 days (immediate family), 3 days (extended)

4. PROFESSIONAL DEVELOPMENT
- Annual learning budget: $5,000 per employee
- Conference attendance: 2 per year
- Tuition reimbursement: up to $10,000/year for approved programs
- Internal mentorship program available

5. WELLNESS PROGRAM
- Gym membership subsidy: $75/month
- Annual wellness screening (on-site)
- Employee Assistance Program (EAP): 24/7 confidential support
- Ergonomic workstation assessment

Policy Type: Benefits
Effective Date: 2025-01-01
Employee Category: Full-time US
Approval Authority: CHRO
Review Cycle: Annual
""",
        },
    ],
    "legal": [
        {
            "filename": "NDA_Standard_Template_2024.txt",
            "content": """MUTUAL NON-DISCLOSURE AGREEMENT

AGREEMENT DATE: [Date]
AGREEMENT ID: NDA-2024-[Number]

PARTIES:
1. [Company Name], a Delaware corporation ("Disclosing Party")
2. [Counterparty Name], a [State/Country] [entity type] ("Receiving Party")

RECITALS
The parties wish to explore a potential business relationship and in connection
therewith may disclose certain confidential and proprietary information.

1. DEFINITION OF CONFIDENTIAL INFORMATION
"Confidential Information" means any information disclosed by either party that is:
(a) marked as confidential or proprietary;
(b) identified as confidential at time of disclosure;
(c) reasonably understood to be confidential given nature and circumstances.

Exclusions:
(i) Information publicly available through no fault of receiving party
(ii) Information known to receiving party prior to disclosure
(iii) Information independently developed without use of confidential information
(iv) Information received from a third party without restriction

2. OBLIGATIONS
The Receiving Party shall:
- Use Confidential Information solely for evaluating the potential relationship
- Restrict access to personnel with need-to-know
- Apply no less than reasonable care (and no less than it applies to its own)
- Not reverse engineer, decompile, or disassemble

3. TERM
- Disclosure period: 2 years from Agreement Date
- Confidentiality obligation: 5 years from date of disclosure
- Trade secrets: protected indefinitely

4. RETURN/DESTRUCTION
Upon written request or termination, receiving party shall return or destroy
all Confidential Information within 30 days and certify destruction in writing.

5. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

Agreement Type: Mutual NDA
Parties: Bilateral
Effective Date: [Date]
Expiration Date: [Date + 2 years]
Jurisdiction: Delaware
Governing Law: Delaware
""",
        },
    ],
    "operations": [
        {
            "filename": "Incident_Response_Playbook_2024.txt",
            "content": """INCIDENT RESPONSE PLAYBOOK - VERSION 4.0

EFFECTIVE DATE: October 1, 2024
OWNER: VP Operations
SLA TARGET: P1 incidents resolved within 4 hours

1. INCIDENT CLASSIFICATION

Priority 1 (Critical):
- Complete service outage affecting >50% of users
- Data breach confirmed
- Revenue-impacting system failure
- Response time: 15 minutes
- Resolution target: 4 hours

Priority 2 (High):
- Partial service degradation affecting >20% of users
- Security vulnerability actively exploited
- Single region failure with no failover
- Response time: 30 minutes
- Resolution target: 8 hours

Priority 3 (Medium):
- Performance degradation affecting <20% of users
- Non-critical system failure
- Response time: 2 hours
- Resolution target: 24 hours

2. ESCALATION PATH
- L1 (NOC): Initial triage and classification
- L2 (Engineering): Technical investigation and fix
- L3 (Architecture): Complex multi-system issues
- Executive: P1 incidents exceeding 2-hour mark

3. COMMUNICATION PROTOCOL
- Internal: Slack #incident-response channel
- Stakeholders: Email every 30 minutes for P1
- Customers: Status page update within 15 minutes
- Post-mortem: Within 5 business days of resolution

4. POST-INCIDENT REVIEW
Required for all P1 and P2 incidents:
- Timeline reconstruction
- Root cause analysis (5 Whys)
- Action items with owners and deadlines
- Process improvement recommendations

Process Name: Incident Management
SLA Target: 4 hours (P1)
Frequency: Continuous
Responsible Team: Operations / SRE
Last Review Date: 2024-10-01
""",
        },
    ],
}


def generate_documents(output_dir: Path) -> None:
    """Generate sample documents for all departments."""
    total = 0
    for department, docs in DOCUMENTS.items():
        dept_dir = output_dir / department
        dept_dir.mkdir(parents=True, exist_ok=True)

        for doc in docs:
            filepath = dept_dir / doc["filename"]
            filepath.write_text(doc["content"], encoding="utf-8")
            total += 1
            print(f"  [{department}] {doc['filename']} ({len(doc['content'])} chars)")

    print(f"\nGenerated {total} sample documents across {len(DOCUMENTS)} departments.")


def generate_manifest(output_dir: Path) -> None:
    """Generate a manifest file listing all sample documents."""
    manifest = []
    for department, docs in DOCUMENTS.items():
        for doc in docs:
            manifest.append({
                "department": department,
                "filename": doc["filename"],
                "path": f"{department}/{doc['filename']}",
                "size_chars": len(doc["content"]),
            })

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written to {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate sample documents")
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT,
        help="Output directory for sample documents",
    )
    args = parser.parse_args()

    print(f"Generating sample documents in: {args.output_dir}")
    print("=" * 60)
    generate_documents(args.output_dir)
    generate_manifest(args.output_dir)
    print("=" * 60)
    print("Done. Upload these via the Streamlit UI or scripts/deploy.py")


if __name__ == "__main__":
    main()
