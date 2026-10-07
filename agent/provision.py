"""Create the Agent37 instance, wait until its agent is healthy, and record its id in .env.

    python3 -m agent.provision

Billable: a default instance is metered per minute and the managed-model budget below
is the most it can spend. Run it only when you mean to.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from agent import clients

log = logging.getLogger("start.provision")

ROOT = Path(__file__).resolve().parent.parent
INSTANCE_NAME = "hackathon-worker"
CREDIT_MICROS = 2_000_000  # $2 of managed model spend, one-time
HEALTH_WAIT_SECONDS = 600
ID_KEY = "AGENT37_INSTANCE_ID"


def with_instance_id(env_text: str, instance_id: str) -> str:
    """Return .env text with the instance id set, replacing an existing line if there is one."""
    line = f"{ID_KEY}={instance_id}"
    lines = env_text.splitlines()
    if any(existing.startswith(f"{ID_KEY}=") for existing in lines):
        lines = [line if existing.startswith(f"{ID_KEY}=") else existing for existing in lines]
    else:
        lines = [*lines, line]
    return "\n".join(lines) + "\n"


def wait_healthy(key: str, instance_id: str, deadline_seconds: int) -> bool:
    started = time.monotonic()
    while time.monotonic() - started < deadline_seconds:
        try:
            if clients.agent37_healthy(key, instance_id):
                return True
        except clients.ClientError as error:
            log.info("not ready yet: %s", error)
        time.sleep(10)
    return False


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    env_path = ROOT / ".env"
    try:
        env = clients.load_env(env_path)
        clients.require(env, "AGENT37_API_KEY")
        instance_id = env.get(ID_KEY) or clients.agent37_create_instance(
            env["AGENT37_API_KEY"], INSTANCE_NAME, CREDIT_MICROS
        )["id"]
    except (clients.ClientError, KeyError) as error:
        log.error("%s", error)
        return 1

    env_path.write_text(with_instance_id(env_path.read_text(), instance_id))
    log.info("instance %s recorded in .env; waiting for the agent to boot", instance_id)
    if not wait_healthy(env["AGENT37_API_KEY"], instance_id, HEALTH_WAIT_SECONDS):
        log.error("instance %s did not report healthy within %ss", instance_id, HEALTH_WAIT_SECONDS)
        return 1
    log.info("instance %s is healthy", instance_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
