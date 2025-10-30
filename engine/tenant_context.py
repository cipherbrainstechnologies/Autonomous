from __future__ import annotations

import os
from typing import Tuple


def resolve_tenant(config: dict) -> Tuple[str, str]:
    """
    Resolve (org_id, user_id) using precedence: ENV > config['tenant'] > defaults.
    """
    org = os.getenv("ORG_ID") or (config.get('tenant', {}) or {}).get('org_id') or "demo-org"
    user = os.getenv("USER_ID") or (config.get('tenant', {}) or {}).get('user_id') or "admin"
    return str(org), str(user)


