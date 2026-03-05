"""
Simple Strands Agent deployed on AgentCore Runtime.

Uses add_async_task / complete_async_task to keep the session alive
during long-running work, preventing the 15-minute idle timeout.

Created using Kiro code assistant.
"""

import threading
import time

from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


# --- Tools ------------------------------------------------------------------

@tool
def start_long_running_job(duration_seconds: int = 60) -> str:
    """Kick off a background job that keeps the session alive.

    The session stays in HealthyBusy state for the entire duration,
    so AgentCore will NOT terminate it after 15 minutes of "idle".
    """
    task_id = app.add_async_task(
        "long_running_job", {"duration": duration_seconds}
    )

    def _work():
        print(f"[job {task_id}] started – running for {duration_seconds}s")
        time.sleep(duration_seconds)  # replace with real work
        app.complete_async_task(task_id)
        print(f"[job {task_id}] completed")

    threading.Thread(target=_work, daemon=True).start()
    return (
        f"Background job started (task_id={task_id}). "
        f"Session will stay alive for {duration_seconds}s."
    )


@tool
def check_job_status() -> str:
    """Return current async-task info and ping status."""
    info = app.get_async_task_info()
    status = app.get_current_ping_status()
    return (
        f"Ping status: {status.value} | "
        f"Active tasks: {info['active_count']} | "
        f"Running jobs: {info['running_jobs']}"
    )


# --- Agent ------------------------------------------------------------------

agent = Agent(
    system_prompt=(
        "You are a helpful assistant. You can start long-running background "
        "jobs and check their status. When asked to do heavy work, use the "
        "start_long_running_job tool so the session stays alive."
    ),
    tools=[start_long_running_job, check_job_status],
)


# --- Entrypoint -------------------------------------------------------------

@app.entrypoint
def invoke(payload, context=None):
    prompt = payload.get("prompt", "Hello!")
    result = agent(prompt)
    return {"response": result.message}


if __name__ == "__main__":
    app.run()
