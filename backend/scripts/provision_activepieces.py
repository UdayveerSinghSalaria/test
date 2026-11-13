#!/usr/bin/env python3
"""
Idempotent provisioning script for Activepieces mail flows.

Creates two flows in the teammate's project:
1. "App Mail Search" — Webhook trigger → gmail_search_mail (inputs from trigger body)
2. "App Mail Get"    — Webhook trigger → gmail_get_mail (message_id from trigger body)

Then IMPORT_FLOW + LOCK_AND_PUBLISH + CHANGE_STATUS ENABLED each flow.
Prints both flow IDs at the end.

Usage:
    python backend/scripts/provision_activepieces.py

Requires in backend/.env:
    ACTIVEPIECES_API_KEY=sk-...
    ACTIVEPIECES_PROJECT_ID=be57Pt3jR0iusqswQv9YY
    ACTIVEPIECES_GMAIL_CONNECTION_ID=3TBdEak6aPrAWUoHS95QM  (externalId)
"""
import os
import sys
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv


# ---- Config ---------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
print(f"DEBUG: ROOT={ROOT}, ENV_PATH={ENV_PATH}, exists={ENV_PATH.exists()}", file=sys.stderr)
load_dotenv(ENV_PATH)

API_KEY = os.getenv("ACTIVEPIECES_API_KEY")
PROJECT_ID = os.getenv("ACTIVEPIECES_PROJECT_ID")
GMAIL_CONNECTION_EXTERNAL_ID = os.getenv("ACTIVEPIECES_GMAIL_CONNECTION_ID")
BASE_URL = os.getenv("ACTIVEPIECES_BASE_URL", "https://cloud.activepieces.com/api/v1")
print(f"DEBUG: API_KEY={'set' if API_KEY else 'MISSING'}, PROJECT_ID={PROJECT_ID}, CONN_ID={GMAIL_CONNECTION_EXTERNAL_ID}", file=sys.stderr)

if not API_KEY or not PROJECT_ID or not GMAIL_CONNECTION_EXTERNAL_ID:
    print("ERROR: Missing required env vars in backend/.env", file=sys.stderr)
    print("  ACTIVEPIECES_API_KEY", file=sys.stderr)
    print("  ACTIVEPIECES_PROJECT_ID", file=sys.stderr)
    print("  ACTIVEPIECES_GMAIL_CONNECTION_ID (externalId from connection list)", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
CLIENT = httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=60.0)

# Flow display names (used for idempotent lookup)
SEARCH_FLOW_DISPLAY = "App Mail Search"
GET_FLOW_DISPLAY = "App Mail Get"

# Gmail piece constants
GMAIL_PIECE = "@activepieces/piece-gmail"
GMAIL_PIECE_VERSION = "0.19.0"
WEBHOOK_PIECE = "@activepieces/piece-webhook"
WEBHOOK_PIECE_VERSION = "0.1.43"

# Step names
SEARCH_STEP = "search_email"
GET_STEP = "get_email"
RESPOND_STEP = "respond"


# ---- Helpers --------------------------------------------------------------

def api_get(path: str, params: Optional[Dict] = None) -> Dict:
    # Exact same call as standalone test
    url = f"{BASE_URL}{path}"
    r = httpx.get(url, params=params, headers=HEADERS, timeout=60.0)
    print(f"DEBUG GET {path}: status={r.status_code}, len={len(r.content)}, text[:200]={r.text[:200]!r}", file=sys.stderr)
    print(f"  Full URL: {r.url}", file=sys.stderr)
    print(f"  Request headers sent: {dict(r.request.headers)}", file=sys.stderr)
    if r.status_code >= 400:
        print(f"GET {path} -> {r.status_code}: {r.text}", file=sys.stderr)
    r.raise_for_status()
    return r.json()


def api_post(path: str, json_body: Dict) -> Dict:
    r = CLIENT.post(path, json=json_body)
    if r.status_code >= 400:
        print(f"POST {path} -> {r.status_code}: {r.text}", file=sys.stderr)
    r.raise_for_status()
    return r.json()


def find_flow_by_display(display_name: str) -> Optional[Dict]:
    """Return flow summary (id, status, publishedVersionId) if exists."""
    data = api_get("/flows", params={"projectId": PROJECT_ID, "limit": 100})
    for f in data.get("data", []):
        if f.get("displayName") == display_name:
            return f
    return None


def get_flow_detail(flow_id: str) -> Dict:
    """Fetch full flow with latest version."""
    return api_get(f"/flows/{flow_id}")


def create_flow(display_name: str) -> Dict:
    """Create a new flow (DRAFT). Returns flow object with id."""
    body = {
        "displayName": display_name,
        "projectId": PROJECT_ID,
    }
    return api_post("/flows", body)


def import_flow(flow_id: str, trigger_json: Dict) -> Dict:
    """Import a trigger definition into the flow (replaces draft)."""
    body = {
        "type": "IMPORT_FLOW",
        "request": {
            "displayName": trigger_json.get("displayName", ""),
            "trigger": trigger_json["trigger"],
        },
    }
    return api_post(f"/flows/{flow_id}", body)


def lock_and_publish(flow_id: str, status: str = "ENABLED") -> Dict:
    """Lock & publish the flow; optionally set initial status."""
    body = {
        "type": "LOCK_AND_PUBLISH",
        "request": {"status": status},
    }
    return api_post(f"/flows/{flow_id}", body)


def change_status(flow_id: str, status: str) -> Dict:
    """Change flow status (ENABLED/DISABLED)."""
    body = {
        "type": "CHANGE_STATUS",
        "request": {"status": status},
    }
    return api_post(f"/flows/{flow_id}", body)


def wait_for_operation(flow_id: str, timeout: float = 30.0) -> None:
    """Poll until operationStatus == NONE."""
    start = time.time()
    while time.time() - start < timeout:
        f = get_flow_detail(flow_id)
        if f.get("operationStatus") == "NONE":
            return
        time.sleep(0.5)
    raise TimeoutError(f"Flow {flow_id} operation did not complete")


def build_search_trigger() -> Dict:
    """Build the 'App Mail Search' trigger + step tree."""
    # All search inputs are dynamic from trigger body
    search_prop_settings = {k: {"type": "DYNAMIC", "schema": {}} for k in [
        "auth", "from", "to", "subject", "content", "has_attachment",
        "attachment_name", "label", "category", "after_date", "before_date",
        "include_spam_trash", "max_results"
    ]}
    trigger_node = {
        "name": "trigger",
        "valid": True,
        "displayName": "catch_webhook",
        "lastUpdatedDate": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "type": "PIECE_TRIGGER",
        "settings": {
            "propertySettings": {"authType": {"type": "MANUAL"}},
            "pieceName": WEBHOOK_PIECE,
            "pieceVersion": WEBHOOK_PIECE_VERSION,
            "triggerName": "catch_webhook",
            "input": {
                "authType": "none",
            },
        },
        "nextAction": {
            "name": SEARCH_STEP,
            "type": "PIECE",
            "valid": True,
            "settings": {
                "input": {
                    "auth": f"{{{{connections['{GMAIL_CONNECTION_EXTERNAL_ID}']}}}}",
                    "from": "{{trigger.body.from}}",
                    "to": "{{trigger.body.to}}",
                    "subject": "{{trigger.body.subject}}",
                    "content": "{{trigger.body.content}}",
                    "has_attachment": "{{trigger.body.has_attachment}}",
                    "attachment_name": "{{trigger.body.attachment_name}}",
                    "label": "{{trigger.body.label}}",
                    "category": "{{trigger.body.category}}",
                    "after_date": "{{trigger.body.after_date}}",
                    "before_date": "{{trigger.body.before_date}}",
                    "include_spam_trash": "{{trigger.body.include_spam_trash}}",
                    "max_results": "{{trigger.body.max_results}}",
                },
                "pieceName": GMAIL_PIECE,
                "actionName": "gmail_search_mail",
                "pieceVersion": GMAIL_PIECE_VERSION,
                "propertySettings": search_prop_settings,
                "errorHandlingOptions": {
                    "retryOnFailure": {"value": False},
                    "continueOnFailure": {"value": False},
                },
            },
            "nextAction": {
                "name": RESPOND_STEP,
                "type": "PIECE",
                "valid": True,
                "displayName": "Return Response",
                "settings": {
                    "input": {
                        "responseType": "json",
                        "fields": {
                            "body": f"{{{{{SEARCH_STEP}.output}}}}",
                            "status": 200,
                        },
                        "respond": "stop",
                    },
                    "pieceName": WEBHOOK_PIECE,
                    "actionName": "return_response",
                    "pieceVersion": WEBHOOK_PIECE_VERSION,
                    "propertySettings": {},
                    "errorHandlingOptions": {
                        "retryOnFailure": {"value": False},
                        "continueOnFailure": {"value": False},
                    },
                },
            },
        },
    }
    return trigger_node


def build_get_trigger() -> Dict:
    """Build the 'App Mail Get' trigger + step tree."""
    # Get step input is dynamic from trigger body
    get_prop_settings = {
        "auth": {"type": "DYNAMIC", "schema": {}},
        "message_id": {"type": "DYNAMIC", "schema": {}},
    }
    trigger_node = {
        "name": "trigger",
        "valid": True,
        "displayName": "catch_webhook",
        "lastUpdatedDate": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "type": "PIECE_TRIGGER",
        "settings": {
            "propertySettings": {"authType": {"type": "MANUAL"}},
            "pieceName": WEBHOOK_PIECE,
            "pieceVersion": WEBHOOK_PIECE_VERSION,
            "triggerName": "catch_webhook",
            "input": {
                "authType": "none",
            },
        },
        "nextAction": {
            "name": GET_STEP,
            "type": "PIECE",
            "valid": True,
            "settings": {
                "input": {
                    "auth": f"{{{{connections['{GMAIL_CONNECTION_EXTERNAL_ID}']}}}}",
                    "message_id": "{{trigger.body.message_id}}",
                },
                "pieceName": GMAIL_PIECE,
                "actionName": "gmail_get_mail",
                "pieceVersion": GMAIL_PIECE_VERSION,
                "propertySettings": get_prop_settings,
                "errorHandlingOptions": {
                    "retryOnFailure": {"value": False},
                    "continueOnFailure": {"value": False},
                },
            },
            "nextAction": {
                "name": RESPOND_STEP,
                "type": "PIECE",
                "valid": True,
                "displayName": "Return Response",
                "settings": {
                    "input": {
                        "responseType": "json",
                        "fields": {
                            "body": f"{{{{{GET_STEP}.output}}}}",
                            "status": 200,
                        },
                        "respond": "stop",
                    },
                    "pieceName": WEBHOOK_PIECE,
                    "actionName": "return_response",
                    "pieceVersion": WEBHOOK_PIECE_VERSION,
                    "propertySettings": {},
                    "errorHandlingOptions": {
                        "retryOnFailure": {"value": False},
                        "continueOnFailure": {"value": False},
                    },
                },
            },
        },
    }
    return trigger_node


def provision_one(display_name: str, trigger_builder) -> str:
    """Idempotently create/import/publish a single flow. Returns flow ID."""
    existing = find_flow_by_display(display_name)
    if existing:
        flow_id = existing["id"]
        print(f"[found] {display_name} -> {flow_id} (status={existing.get('status')})")
        # If disabled, enable it
        if existing.get("status") == "DISABLED":
            print(f"  enabling...")
            change_status(flow_id, "ENABLED")
            wait_for_operation(flow_id)
        return flow_id

    print(f"[create] {display_name}")
    flow = create_flow(display_name)
    flow_id = flow["id"]
    print(f"  flow created: {flow_id}")

    # Build & import
    trigger = trigger_builder()
    import_flow(flow_id, {"displayName": display_name, "trigger": trigger})
    wait_for_operation(flow_id)

    # Lock & publish (ENABLED)
    lock_and_publish(flow_id, "ENABLED")
    wait_for_operation(flow_id)

    # Verify
    final = get_flow_detail(flow_id)
    print(f"  published: id={final.get('publishedVersionId')} status={final.get('status')}")
    return flow_id


# ---- Main -----------------------------------------------------------------

def main():
    print("=== Activepieces Mail Flow Provisioning ===")
    print(f"Project: {PROJECT_ID}")
    print(f"Gmail connection (externalId): {GMAIL_CONNECTION_EXTERNAL_ID}")
    print()

    search_id = provision_one(SEARCH_FLOW_DISPLAY, build_search_trigger)
    print()
    get_id = provision_one(GET_FLOW_DISPLAY, build_get_trigger)

    print()
    print("=== Done ===")
    print(f"SEARCH_FLOW_ID={search_id}")
    print(f"GET_FLOW_ID={get_id}")
    print()
    print("Add these to backend/.env:")
    print(f"ACTIVEPIECES_SEARCH_FLOW_ID={search_id}")
    print(f"ACTIVEPIECES_GET_FLOW_ID={get_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)