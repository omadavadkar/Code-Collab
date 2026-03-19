// Unified initializer: CodeMirror + WebSocket chat/collab
(function () {
  console.log('[CodeCollab] script.js loaded');

  let editor = null;
  let socket = null;
  let applyingRemote = false;
  let term = null;

  // You can override WS base by defining window.WS_BASE before this script runs
    const DEFAULT_WS_BASE = 'ws://localhost:8000'; // e.g., ws://localhost:8000
  const params = new URLSearchParams(window.location.search);
  const roomFromQuery = params.get('room');
  const fileToLoad = params.get('file'); // e.g., /static/index.html
  const langParam = params.get('lang'); // e.g., html, python, css, js
  const roomId = roomFromQuery || 'test-room';

  function debounce(fn, wait) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function initEditor() {
    const textarea = document.getElementById('editor');
    if (!textarea) {
      console.error('[CodeCollab] #editor not found in DOM');
      return;
    }
    if (typeof CodeMirror === 'undefined') {
      console.error('[CodeCollab] CodeMirror is not loaded. Check CDN order/connectivity.');
      return;
    }

    const mode = (langParam === 'html') ? 'htmlmixed'
              : (langParam === 'css') ? 'css'
              : (langParam === 'js' || langParam === 'javascript') ? 'javascript'
              : 'python';

    editor = CodeMirror.fromTextArea(textarea, {
      mode,
      lineNumbers: true,
      theme: 'material-darker',
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      lineWrapping: false,
      styleActiveLine: { nonEmpty: true },
      matchBrackets: true,
      autoCloseBrackets: true,
      autofocus: true,
      keyMap: 'sublime'
    });

    // Debounced broadcast to reduce spam over WS
    const broadcastChange = debounce(() => {
        if (!socket || typeof socket.emit !== 'function') return;
      if (applyingRemote) return; // ignore changes we applied from remote
      const code = editor.getValue();
        try { socket.emit('code_update', { room: roomId, text: code }); } catch (e) { console.warn('[CodeCollab] emit failed', e); }
    }, 200);

    editor.on('change', broadcastChange);

    // Load exact file content if requested
    if (fileToLoad) {
      fetch(fileToLoad, { cache: 'no-store' })
        .then(r => r.ok ? r.text() : Promise.reject(new Error(`${r.status} ${r.statusText}`)))
        .then(txt => {
          editor.setValue(txt);
        })
        .catch(err => {
          console.error('[CodeCollab] Failed to load file', fileToLoad, err);
        });
    } else {
      // Example content for first load
      if (!editor.getValue()) {
        editor.setValue(`# Welcome to Code Collab (VS Code-like)\n` +
          `def greet(name: str) -> None:\n` +
          `    print(f"Hello, {name}")\n\n` +
          `greet("World")\n`);
      }
    }

    window.editor = editor; // for console access
    console.log('[CodeCollab] CodeMirror initialized');
  }

  function appendChatMessage(msg) {
    const box = document.getElementById('messages');
    if (!box) return;
    const p = document.createElement('p');
    p.textContent = msg;
    box.appendChild(p);
    box.scrollTop = box.scrollHeight;
  }

  function buildWsUrl() {
    const base = window.WS_BASE || DEFAULT_WS_BASE; // e.g., ws://localhost:8000
    return `${base}/ws/${roomId}`;
  }

  function initSocket() {
      if (typeof io === 'undefined') {
        console.error('[CodeCollab] Socket.IO client not loaded');
        return;
      }
      socket = io({ transports: ['polling', 'websocket'] });
      socket.on('connect', () => {
        console.log('✅ Connected to Socket.IO', socket.id);
        socket.emit('join', { room: roomId });
      });
      socket.on('disconnect', (reason) => {
        console.warn('⚠️ Socket.IO disconnected', reason);
      });
      socket.on('connect_error', (err) => {
        console.error('❌ Socket.IO connect_error', err);
      });

      socket.on('code_update', (payload) => {
        const text = (payload && payload.text) || '';
        if (editor && typeof text === 'string') {
          if (editor.getValue() !== text) {
            applyingRemote = true;
            editor.setValue(text);
            applyingRemote = false;
          }
        }
      });
      socket.on('chat_message', (payload) => {
        const message = (payload && payload.message) || '';
        if (message) appendChatMessage(message);
      });
      socket.on('chat_history', (payload) => {
        const msgs = (payload && payload.messages) || [];
        if (Array.isArray(msgs) && msgs.length) {
          msgs.forEach(m => appendChatMessage(m));
        }
      });
      socket.on('terminal_output', (payload) => {
        if (term && payload && payload.text) {
          term.write(payload.text);
        }
      });
      socket.on('terminal_clear', () => {
        if (term) term.clear();
      });
  }

  function initTerminal() {
    const termContainer = document.getElementById('terminal');
    if (!termContainer || typeof Terminal === 'undefined') {
      console.warn('[CodeCollab] Terminal element or library not found');
      return;
    }
    term = new Terminal({
      cursorBlink: true,
      theme: { background: '#000' }
    });
    const fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    term.open(termContainer);
    fitAddon.fit();
    
    // When window resizes, resize terminal
    window.addEventListener('resize', () => {
      fitAddon.fit();
    });

    // Send keystrokes to the server and do local echo since we lack a true PTY
    term.onData(data => {
      if (socket && typeof socket.emit === 'function') {
        socket.emit('terminal_input', { room: roomId, text: data });
      }
      
      // Basic local echo
      if (data === '\\r') {
        term.write('\\r\\n');
      } else if (data === '\\x7f' || data === '\\b') { // Backspace
        term.write('\\b \\b');
      } else {
        term.write(data);
      }
    });
    
    term.writeln('Terminal ready. Click "Run Code" to start.');
  }

  // Expose button handlers expected by HTML
  window.logCode = function () {
    if (editor) console.log(editor.getValue());
    else console.warn('[CodeCollab] editor not ready');
  };
  window.sendChat = function () {
    const input = document.getElementById('chatInput');
    if (!input) return;
    const message = (input.value || '').trim();
    if (!message) return;
    try {
        if (socket && typeof socket.emit === 'function') {
          socket.emit('chat_message', { room: roomId, message });
          appendChatMessage(message); // echo locally
        } else {
          console.warn('[CodeCollab] Socket.IO not connected');
        }
    } finally {
      input.value = '';
    }
  };
  // Allow pressing Enter to send chat
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const active = document.activeElement;
      if (active && active.id === 'chatInput') {
        e.preventDefault();
        window.sendChat();
      }
    }
  });
    window.runCode = function () {
    if (!editor) {
      console.warn('[CodeCollab] editor not ready');
      return;
    }
    if (!socket || typeof socket.emit !== 'function') {
      console.warn('[CodeCollab] socket not connected');
      if (term) term.writeln('\\r\\nError: Not connected to server.');
      return;
    }

    const code = editor.getValue();
    const languageSelect = document.getElementById("language");
    const language = languageSelect ? languageSelect.value : "python";

    if (term) {
      term.clear();
      term.writeln(`\\r\\nStarting ${language} process...\\r\\n`);
      term.focus();
    }

    socket.emit('start_run', { room: roomId, code, language });
  };


  document.addEventListener('DOMContentLoaded', () => {
    console.log('[CodeCollab] DOMContentLoaded');
    initEditor();
    initTerminal();
    initSocket();
  });
})();