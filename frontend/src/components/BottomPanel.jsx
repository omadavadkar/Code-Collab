export default function BottomPanel({ tabs, output }) {
  return (
    <section className="h-full bg-vscode-panel border-t border-vscode-border flex flex-col">
      <div className="h-10 border-b border-vscode-border flex items-center px-3 gap-4 text-sm">
        {tabs.map((tab, idx) => (
          <button key={tab} className={idx === 1 ? "text-white" : "text-vscode-muted hover:text-white"}>
            {tab}
          </button>
        ))}
      </div>
      <pre className="flex-1 m-0 p-3 overflow-auto text-sm font-mono whitespace-pre-wrap scrollbar-dark">{output}</pre>
    </section>
  );
}
