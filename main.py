import uuid
from flask import Flask, redirect, url_for, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, emit
import subprocess
import tempfile
import os
import sys
import shutil

# Initialize the Flask application
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
room_states: dict[str, str] = {}
room_chats: dict[str, list[str]] = {}

# 1. Store room data temporarily (using a Python dictionary)
# This dictionary will hold our room data while the server is running.
rooms_data = {}
running_processes = {}  # Maps room_id -> (subprocess.Popen, temp_dir_path)

# --- HTML Templates ---
# For simplicity, we'll keep the HTML directly in our Python file.

# HTML for the home page to create or join a room
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chat Rooms</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        .container { max-width: 480px; margin: auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px; }
        .button { background-color: #007BFF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }
        form { margin-top: 20px; }
        input[type="text"] { padding: 8px 10px; width: 70%; max-width: 320px; }
        button[type="submit"], .button { cursor: pointer; border: none; }
        .hint { color: #555; font-size: 0.9rem; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome!</h1>
        <p>Create a new chat room or join an existing one.</p>
        <a href="{{ url_for('create_room') }}" class="button">Create a New Room</a>

        <h3 style="margin-top:28px;">Or join an existing room</h3>
        <form action="/editor" method="get">
            <input type="text" name="room" placeholder="Enter Room ID" required />
           
            <button type="submit" class="button">Open Editor</button>
        </form>
        <div class="hint">Share the same Room ID with your friends to code together.</div>
    </div>
</body>
</html>
"""

# HTML for the room page
ROOM_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Room: {{ room_name }}</title>
    <style>
        body { font-family: sans-serif; }
        .container { max-width: 600px; margin: auto; padding: 20px; }
        h1 { color: #333; }
        .room-id { font-family: monospace; background-color: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
        .button { background-color: #007BFF; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; display: inline-block; }
        .button:hover { background-color: #0069d9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Room: {{ room_name }}</h1>
        <p>Your unique room ID is: <strong class="room-id">{{ room_id }}</strong></p>
        <p>Share this ID with others to let them join!</p>
        <p>
            <a href="/editor?room={{ room_id }}&file=/static/index.html=html" class="button">Open Collaborative Editor</a>
        </p>
        <a href="/"> &larr; Back to Home</a>
    </div>
</body>
</html>
"""

# --- Route Definitions ---

@app.route("/")
def home():
    """Renders the home page."""
    return render_template_string(HOME_PAGE_TEMPLATE)

@app.route("/create_room")
def create_room():
    """
    Creates a new room, stores its data, and redirects the user.
    """
    # 1. Generate a unique room ID using Python's uuid module
    # We take the first 8 characters for a shorter, more user-friendly URL.
    new_room_id = str(uuid.uuid4())[:8]
    
    # 3. Store room data in our dictionary
    rooms_data[new_room_id] = {
        "name": f"Chat Room {len(rooms_data) + 1}",
        "users": [],
        "messages": []
    }
    
    print(f"Room created: {new_room_id}. Current rooms: {list(rooms_data.keys())}")
    
    # 2. Redirect the user to the new room's URL
    return redirect(url_for('room_page', room_id=new_room_id))

@app.route("/room/<string:room_id>")
def room_page(room_id):
    """
    Displays the page for a specific room.
    """
    # Check if the room ID exists in our temporary storage
    if room_id not in rooms_data:
        return "<h1>Room not found!</h1><a href='/'>Go Home</a>", 404
    
    # Get the room's data
    room_info = rooms_data.get(room_id)
    
    return render_template_string(
        ROOM_PAGE_TEMPLATE, 
        room_id=room_id, 
        room_name=room_info.get("name")
    )

# Serve the CodeMirror editor page
@app.route("/editor")
def editor_page():
    # This will serve my_fastapi_app/static/index.html
    return send_from_directory(app.static_folder, 'index.html')

# Support relative links in index.html (style.css, script.js) without changing HTML
@app.route('/style.css')
def root_style_css():
    return send_from_directory(app.static_folder, 'style.css')

@app.route('/script.js')
def root_script_js():
    return send_from_directory(app.static_folder, 'script.js')

# --- Socket.IO Events (no Uvicorn required) ---

@socketio.on('start_run')
def handle_start_run(data):
    room = (data or {}).get('room')
    if not room: return
    
    code = (data or {}).get("code", "")
    language = (data or {}).get("language", "python")

    if room in running_processes:
        proc, stale_tmp = running_processes[room]
        try: proc.kill()
        except: pass
        try: shutil.rmtree(stale_tmp, ignore_errors=True)
        except: pass
        del running_processes[room]

    tmpdir = tempfile.mkdtemp()
    
    if language == "python":
        file_path = os.path.join(tmpdir, "main.py")
        with open(file_path, "w") as f: f.write(code)
        # Use -u for unbuffered Python output
        cmd = [sys.executable, "-u", file_path]
        
    elif language == "cpp":
        source_path = os.path.join(tmpdir, "main.cpp")
        exe_name = "main.exe" if os.name == "nt" else "main.out"
        exe_path = os.path.join(tmpdir, exe_name)
        with open(source_path, "w") as f: f.write(code)
        compile_result = subprocess.run(["g++", source_path, "-o", exe_path], capture_output=True, text=True)
        if compile_result.returncode != 0:
            socketio.emit('terminal_output', {'text': f"{compile_result.stderr}\r\n".replace('\n', '\r\n')}, to=room)
            shutil.rmtree(tmpdir, ignore_errors=True)
            return
        cmd = [exe_path]
        
    elif language == "java":
        source_path = os.path.join(tmpdir, "Main.java")
        with open(source_path, "w") as f: f.write(code)
        compile_result = subprocess.run(["javac", source_path], capture_output=True, text=True)
        if compile_result.returncode != 0:
            socketio.emit('terminal_output', {'text': f"{compile_result.stderr}\r\n".replace('\n', '\r\n')}, to=room)
            shutil.rmtree(tmpdir, ignore_errors=True)
            return
        cmd = ["java", "-cp", tmpdir, "Main"]
    else:
        return

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=tmpdir,
            bufsize=0 # important for immediate output
        )
        running_processes[room] = (proc, tmpdir)
        
        def read_output(p, r, tdir):
            while True:
                char = p.stdout.read(1)
                if not char:
                    break
                try:
                    text = char.decode('utf-8', errors='replace')
                    if text == '\n': text = '\r\n'
                    socketio.emit('terminal_output', {'text': text}, to=r)
                except:
                    pass
            p.wait()
            socketio.emit('terminal_output', {'text': f'\r\n[Process exited with code {p.returncode}]\r\n'}, to=r)
            if running_processes.get(r, (None, None))[0] == p:
                del running_processes[r]
                try: shutil.rmtree(tdir, ignore_errors=True)
                except: pass

        socketio.start_background_task(read_output, proc, room, tmpdir)
        
    except Exception as e:
        socketio.emit('terminal_output', {'text': f'\r\nError: {str(e)}\r\n'}, to=room)

@socketio.on('terminal_input')
def handle_terminal_input(data):
    room = (data or {}).get('room')
    text = (data or {}).get('text', '')
    if not room or not text: return
    
    if room in running_processes:
        proc, _ = running_processes[room]
        try:
            if proc.poll() is None:
                # Replace carriage return from xterm with newline for subprocess
                mapped_text = text.replace('\\r', '\\n')
                proc.stdin.write(mapped_text.encode('utf-8'))
                proc.stdin.flush()
        except Exception as e:
            print("Error writing to stdin", e)



@socketio.on('connect')
def on_connect():
    # Optionally log connections
    pass

@socketio.on('disconnect')
def on_disconnect():
    # Optionally log disconnects
    pass

@socketio.on('join')
def handle_join(data):
    room = (data or {}).get('room')
    if not room:
        return
    join_room(room)
    # Send current room state to the newly joined client, if any
    current = room_states.get(room, '')
    if current:
        emit('code_update', {'text': current})
    # Send recent chat history to the newly joined client
    history = room_chats.get(room, [])
    if history:
        emit('chat_history', {'messages': history})

@socketio.on('code_update')
def handle_code_update(data):
    room = (data or {}).get('room')
    text = (data or {}).get('text', '')
    if not room:
        return
    # Persist the latest state for this room for future joiners
    room_states[room] = text
    # Broadcast to others in the room
    emit('code_update', {'text': text}, to=room, include_self=False)

@socketio.on('chat_message')
def handle_chat_message(data):
    room = (data or {}).get('room')
    message = (data or {}).get('message', '')
    if not room:
        return
    # Store chat history (keep last 100 messages)
    msgs = room_chats.setdefault(room, [])
    msgs.append(message)
    if len(msgs) > 100:
        del msgs[:-100]
    # Broadcast to others in the room
    emit('chat_message', {'message': message}, to=room, include_self=False)

# --- Main Entry Point ---

if __name__ == "__main__":
    # Run via SocketIO so you don't need Uvicorn; will use long-polling by default.
    # For better performance, 'pip install eventlet' and pass 'socketio.run(app, debug=True)' (eventlet is detected automatically).
    socketio.run(app, debug=True)