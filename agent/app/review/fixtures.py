"""Built-in demo pull request used by the fixture provider and tests.

The demo PR intentionally introduces a spread of violations across all
review categories so the engine's output is deterministic and inspectable
without any GitHub access.
"""

from __future__ import annotations

from app.review.review_models import ChangedFile, PullRequestData

DEMO_REPO = "waste-iq/demo"
DEMO_BRANCH = "feature/demo-payments"

PAYMENTS_PY = """\"\"\"Payment processing endpoints for the demo.\"\"\"

import json

from fastapi import APIRouter

from app.db.session import SessionLocal

router = APIRouter(tags=["payments"])


@router.get("/payments/{payment_id}")
async def get_payment():
    db = SessionLocal()
    payload = json.loads(await request.body())
    data = eval(payload.get("expr", "1"))
    return {"payment_id": payment_id}


def refunds_by_amount(amount):
    result = []
    db = SessionLocal()
    payments = db.query(Payment).all()
    for payment in payments:
        customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
        if customer and customer.amount == amount:
            result.append(payment)
    return result


def lookup_item(item_id):
    if result == None:
        return None
    return {item_id: result}


def safe_load(text):
    try:
        return json.loads(text)
    except:
        return None


class PaymentLedger:
    pass
"""

ANALYTICS_PY = """from app.db.session import SessionLocal


def count_events(events=[]):
    events.append("event")
    return len(events)
"""

TEST_PAYMENTS_PY = """import time

import pytest


@pytest.mark.skip(reason="flaky")
def test_that_will_never_run():
    assert True


def test_payments_after_delay():
    time.sleep(2)
    assert True
"""

PAYMENT_LIST_JSX = """import React from "react";

export function PaymentList({ payments }) {
  return (
    <ul>
      {payments.map((payment) => (
        <li>
          {payment.amount} <a href={payment.url} target="_blank">{payment.name}</a>
        </li>
      ))}
    </ul>
  );
}

export function RawNote({ html }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
"""

DEMO_FILES: list[ChangedFile] = [
    ChangedFile(path="backend/app/routes/payments.py", status="added", content=PAYMENTS_PY),
    ChangedFile(path="backend/app/routes/analytics.py", status="added", content=ANALYTICS_PY),
    ChangedFile(path="backend/tests/test_payments.py", status="added", content=TEST_PAYMENTS_PY),
    ChangedFile(
        path="frontend/src/components/PaymentList.jsx", status="added", content=PAYMENT_LIST_JSX
    ),
]


def demo_pull_request(repo_full_name: str = DEMO_REPO) -> PullRequestData:
    return PullRequestData(
        number=1,
        repo_full_name=repo_full_name,
        title="demo: introduce payments and analytics modules",
        branch=DEMO_BRANCH,
        base_branch="main",
        commit_sha="1a2b3c4d5e6f",
        author="demo-author",
        state="open",
        files=[file.model_copy(deep=True) for file in DEMO_FILES],
    )


def demo_patch() -> str:
    """Unified diff for the demo PR (used to exercise the diff parser)."""
    lines = [
        "diff --git a/backend/app/routes/payments.py b/backend/app/routes/payments.py",
        "new file mode 100644",
        "--- /dev/null",
        "+++ b/backend/app/routes/payments.py",
    ]
    content_lines = PAYMENTS_PY.rstrip("\n").splitlines()
    lines.append(f"@@ -0,0 +1,{len(content_lines)} @@")
    lines.extend(f"+{line}" for line in content_lines)
    for path in ("backend/app/routes/analytics.py", "backend/tests/test_payments.py"):
        content = {
            "backend/app/routes/analytics.py": ANALYTICS_PY,
            "backend/tests/test_payments.py": TEST_PAYMENTS_PY,
        }[path]
        lines.append(f"diff --git a/{path} b/{path}")
        lines.append("new file mode 100644")
        lines.append("--- /dev/null")
        lines.append(f"+++ b/{path}")
        content_lines = content.rstrip("\n").splitlines()
        lines.append(f"@@ -0,0 +1,{len(content_lines)} @@")
        lines.extend(f"+{line}" for line in content_lines)
    return "\n".join(lines)
