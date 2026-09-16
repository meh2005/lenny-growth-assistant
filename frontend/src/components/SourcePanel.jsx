function SourcePanel({ sources = [] }) {
  if (!sources.length) {
    return (
      <aside className="source-panel">
        <div className="source-header">
          <h3>Sources</h3>
        </div>

        <p className="source-empty">
          Sources will appear here when the assistant uses transcript evidence.
        </p>
      </aside>
    );
  }

  return (
    <aside className="source-panel">
      <div className="source-header">
        <h3>Sources</h3>
        <span>{sources.length}</span>
      </div>

      <div className="source-list">
        {sources.map((source, index) => (
          <div
            className="source-card"
            key={`${source.source_id}-${source.chunk_index}-${index}`}
          >
            <div className="source-title">
              Source {index + 1}
            </div>

            <div className="source-episode">
              {source.episode_title}
            </div>

            <div className="source-meta">
              {source.source_id} · Chunk {source.chunk_index}
            </div>

            <p className="source-content">
              {source.content}
            </p>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default SourcePanel;