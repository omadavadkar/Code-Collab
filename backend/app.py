import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Set

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "code-collab-secret"

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# In-memory room state.
room_users: Dict[str, Set[str]] = {}
room_code: Dict[str, str] = {}
room_chat: Dict[str, List[dict]] = {}

SUPPORTED_LANGUAGES = {"python", "cpp", "java"}
EXECUTION_TIMEOUT_SECONDS = 3


def run_code(language: str, code: str) -> str:
    """Compile/execute code with strict timeout and temp file cleanup."""
    temp_dir = tempfile.mkdtemp(prefix="code-collab-")
    try:
        if language == "python":
            source_file = os.path.join(temp_dir, "temp.py")
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)
            command = ["python", source_file]
            output = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                cwd=temp_dir,
            )
            return (output.stdout or "") + (output.stderr or "")

        if language == "cpp":
            source_file = os.path.join(temp_dir, "temp.cpp")
            binary_file = os.path.join(temp_dir, "temp.out")
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)

            compile_proc = subprocess.run(
                ["g++", source_file, "-o", binary_file],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                cwd=temp_dir,
            )
            if compile_proc.returncode != 0:
                return compile_proc.stderr or "C++ compilation failed."

            exec_proc = subprocess.run(
                [binary_file],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                cwd=temp_dir,
            )
            return (exec_proc.stdout or "") + (exec_proc.stderr or "")

        if language == "java":
            source_file = os.path.join(temp_dir, "Main.java")
            with open(source_file, "w", encoding="utf-8") as f:
                f.write(code)

            compile_proc = subprocess.run(
                ["javac", source_file],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                cwd=temp_dir,
            )
            if compile_proc.returncode != 0:
                return compile_proc.stderr or "Java compilation failed."

            exec_proc = subprocess.run(
                ["java", "-cp", temp_dir, "Main"],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                cwd=temp_dir,
            )
            return (exec_proc.stdout or "") + (exec_proc.stderr or "")

        return "Unsupported language."
    except subprocess.TimeoutExpired:
        return "Execution timed out after 3 seconds."
    except Exception:
        app.logger.exception("Unhandled error while executing code.")
        return "Execution failed due to an internal error."
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/run")
def execute_code():
    """Execute user code and return output."""
    data = request.get_json(silent=True) or {}
    language = (data.get("language") or "").strip().lower()
    code = data.get("code") or ""

    if language not in SUPPORTED_LANGUAGES:
        return jsonify({"error": "Invalid language. Use python, cpp, or java."}), 400
    if not isinstance(code, str):
        return jsonify({"error": "Code must be a string."}), 400

    output = run_code(language, code)
    return jsonify({"output": output})


@socketio.on("join_room")
def handle_join_room(data):
    room_id = (data or {}).get("room_id")
    username = (data or {}).get("username", "Anonymous")
    if not room_id:
        return

    join_room(room_id)
    users = room_users.setdefault(room_id, set())
    users.add(username)

    emit(
        "room_state",
        {
            "users": sorted(list(users)),
            "code": room_code.get(room_id, ""),
            "messages": room_chat.get(room_id, []),
        },
    )
    emit("user_join", {"username": username, "users": sorted(list(users))}, to=room_id)


@socketio.on("code_change")
def handle_code_change(data):
    room_id = (data or {}).get("room_id")
    code = (data or {}).get("code", "")
    language = (data or {}).get("language", "python")
    if not room_id:
        return

    room_code[room_id] = code
    emit(
        "code_change",
        {"code": code, "language": language},
        to=room_id,
        include_self=False,
    )


@socketio.on("send_message")
def handle_send_message(data):
    room_id = (data or {}).get("room_id")
    username = (data or {}).get("username", "Anonymous")
    message = (data or {}).get("message", "")
    if not room_id or not message:
        return

    room_messages = room_chat.setdefault(room_id, [])
    payload = {"username": username, "message": message}
    room_messages.append(payload)
    room_chat[room_id] = room_messages[-200:]
    emit("send_message", payload, to=room_id)


@socketio.on("leave_room")
def handle_leave_room(data):
    room_id = (data or {}).get("room_id")
    username = (data or {}).get("username", "Anonymous")
    if not room_id:
        return

    leave_room(room_id)
    users = room_users.get(room_id, set())
    users.discard(username)

    if not users:
        room_users.pop(room_id, None)
        room_code.pop(room_id, None)
        room_chat.pop(room_id, None)

    emit("user_leave", {"username": username, "users": sorted(list(users))}, to=room_id)


@app.get("/health")
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
