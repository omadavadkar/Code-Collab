import BottomPanel from "./components/BottomPanel";
import EditorArea from "./components/EditorArea";
import FileExplorer from "./components/FileExplorer";
import TeamChatSidebar from "./components/TeamChatSidebar";
import { panelTabs, editorTabs, fileTree } from "./data/mockData";
import { useCollabSession } from "./hooks/useCollabSession";

export default function App() {
  const { roomId, language, setLanguage, code, updateCode, users, messages, sendMessage, output, executeCode } = useCollabSession();

  return (
    <main className="h-screen bg-vscode-bg text-vscode-text grid grid-rows-[1fr_220px]">
      <div className="grid grid-cols-[260px_1fr_360px] min-h-0">
        <FileExplorer files={fileTree} />
        <EditorArea
          tabs={editorTabs}
          language={language}
          code={code}
          onCodeChange={updateCode}
          onLanguageChange={setLanguage}
          roomId={roomId}
          onRun={executeCode}
        />
        <TeamChatSidebar users={users} messages={messages} onSendMessage={sendMessage} />
      </div>
      <BottomPanel tabs={panelTabs} output={output} />
    </main>
  );
}
