import { useState } from "react";
import { X, Code2, Eye } from "lucide-react";

function ArtifactViewer({ artifact, onClose }) {
  const [view, setView] = useState("preview");

  if (!artifact) {
    return null;
  }

  return (
    <aside className="artifact-panel">
      <div className="artifact-header">
        <div>
          <h3>{artifact.title || "Artifact"}</h3>
          <p>{artifact.type || "Generated content"}</p>
        </div>

        <button
          className="artifact-close"
          onClick={onClose}
          title="Close artifact"
        >
          <X size={18} />
        </button>
      </div>

      <div className="artifact-toolbar">
        <button
          className={view === "preview" ? "active" : ""}
          onClick={() => setView("preview")}
        >
          <Eye size={15} />
          Preview
        </button>

        <button
          className={view === "code" ? "active" : ""}
          onClick={() => setView("code")}
        >
          <Code2 size={15} />
          Code
        </button>
      </div>

      <div className="artifact-content">
        {view === "preview" ? (
          <iframe
            title="Artifact preview"
            sandbox=""
            srcDoc={artifact.html}
            className="artifact-frame"
          />
        ) : (
          <pre className="artifact-code">
            {artifact.html}
          </pre>
        )}
      </div>
    </aside>
  );
}

export default ArtifactViewer;