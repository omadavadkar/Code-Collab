import { useState } from "react";

export default function TeamChatSidebar({ users, messages, onSendMessage }) {
  const [draft, setDraft] = useState("");

  const handleSend = () => {
    if (!draft.trim()) return;
    onSendMessage(draft);
    setDraft("");
  };

  return (
    <aside className="h-full bg-vscode-sidebar p-3 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl">Team Sync</h2>
        <div className="flex items-center gap-2">
          <button className="w-9 h-9 rounded-full bg-[#3a3a3a]">📹</button>
          <button className="w-9 h-9 rounded-full bg-[#3a3a3a]">🎤</button>
          <button className="px-3 h-9 rounded bg-red-600">End Call</button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        {users.map((user) => (
          <div key={user} className="bg-[#2a2a2a] border border-vscode-border rounded p-2 text-sm">
            {user}
          </div>
        ))}
      </div>

      <div className="border-t border-vscode-border pt-3 flex-1 flex flex-col min-h-0">
        <h3 className="text-vscode-muted text-xs tracking-wide mb-2">COLLABORATION / CHAT</h3>
        <div className="flex-1 overflow-y-auto scrollbar-dark space-y-2 pr-1">
          {messages.map((msg, idx) => (
            <div key={`${msg.username}-${idx}`} className="text-sm">
              <span className="font-semibold">{msg.username}: </span>
              <span>{msg.message}</span>
            </div>
          ))}
        </div>
        <div className="mt-3 flex gap-2">
          <input
            className="flex-1 bg-[#2b2b2b] border border-vscode-border rounded px-2 py-1"
            placeholder="Type message..."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && handleSend()}
          />
          <button onClick={handleSend} className="bg-vscode-accent px-3 rounded">
            Send
          </button>
        </div>
      </div>
    </aside>
  );
}
