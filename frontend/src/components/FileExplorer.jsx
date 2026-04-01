function TreeNode({ node, depth = 0 }) {
  const hasChildren = Array.isArray(node.children) && node.children.length > 0;
  return (
    <div>
      <div className="py-1 text-sm" style={{ paddingLeft: `${depth * 12}px` }}>
        {hasChildren ? "▾ " : "• "}
        {node.name}
      </div>
      {hasChildren && node.children.map((child) => <TreeNode key={`${node.name}-${child.name}`} node={child} depth={depth + 1} />)}
    </div>
  );
}

export default function FileExplorer({ files }) {
  return (
    <aside className="h-full bg-vscode-sidebar border-r border-vscode-border p-3 overflow-y-auto scrollbar-dark">
      <h2 className="text-xs tracking-wide text-vscode-muted mb-3">EXPLORER</h2>
      {files.map((node) => (
        <TreeNode key={node.name} node={node} />
      ))}
    </aside>
  );
}
