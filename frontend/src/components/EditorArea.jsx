import Editor from "@monaco-editor/react";

export default function EditorArea({ tabs, language, code, onCodeChange, onLanguageChange, roomId, onRun }) {
  const monacoLanguage = language === "cpp" ? "cpp" : language;

  return (
    <section className="h-full flex flex-col bg-vscode-bg border-r border-vscode-border">
      <div className="h-10 border-b border-vscode-border flex items-center px-3 gap-2 text-sm bg-vscode-panel">
        {tabs.map((tab) => (
          <button key={tab} className="px-3 py-1 rounded bg-[#2d2d2d] hover:bg-[#383838] text-vscode-text">
            {tab}
          </button>
        ))}
      </div>

      <div className="h-10 border-b border-vscode-border px-3 flex items-center justify-between bg-vscode-panel text-sm">
        <div className="flex items-center gap-3">
          <span className="text-vscode-muted">Room:</span>
          <span className="font-mono">{roomId}</span>
          <select
            className="bg-[#333] border border-vscode-border rounded px-2 py-1 text-sm"
            value={language}
            onChange={(event) => onLanguageChange(event.target.value)}
          >
            <option value="python">Python</option>
            <option value="cpp">C++</option>
            <option value="java">Java</option>
          </select>
        </div>
        <button onClick={onRun} className="bg-vscode-accent hover:bg-[#0a86d0] text-white px-4 py-1 rounded">
          Run
        </button>
      </div>

      <div className="flex-1">
        <Editor
          height="100%"
          theme="vs-dark"
          language={monacoLanguage}
          value={code}
          onChange={(value) => onCodeChange(value ?? "")}
          options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false, automaticLayout: true }}
        />
      </div>
    </section>
  );
}
