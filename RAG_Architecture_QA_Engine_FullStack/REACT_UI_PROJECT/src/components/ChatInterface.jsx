import React, { useState } from "react";

export default function ChatInterface() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [showDebug, setShowDebug] = useState(false);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/semantic-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "2rem auto",
        padding: "1.5rem",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: "#ffffff",
        borderRadius: "12px",
        boxShadow:
          "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
      }}
    >
      <h2
        style={{
          marginTop: 0,
          color: "#1e293b",
          borderBottom: "2px solid #f1f5f9",
          paddingBottom: "0.75rem",
        }}
      >
        AI RAG Q&A Assistant
      </h2>

      {/* Search Input Form */}
      <form
        onSubmit={handleAsk}
        style={{
          display: "flex",
          gap: "10px",
          marginTop: "1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your documents..."
          style={{
            flex: 1,
            padding: "12px 16px",
            fontSize: "1rem",
            border: "1px solid #cbd5e1",
            borderRadius: "8px",
            outline: "none",
            transition: "border-color 0.2s",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "12px 24px",
            fontSize: "1rem",
            fontWeight: "600",
            backgroundColor: loading ? "#94a3b8" : "#2563eb",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            cursor: loading ? "not-allowed" : "pointer",
            transition: "background-color 0.2s",
          }}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "#fef2f2",
            border: "1px solid #fca5a5",
            borderRadius: "8px",
            color: "#991b1b",
            marginBottom: "1.5rem",
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div
          style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}
        >
          {/* Synthesized Answer Card */}
          <div
            style={{
              padding: "1.25rem",
              backgroundColor: "#f8fafc",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
            }}
          >
            <h3
              style={{
                margin: "0 0 0.75rem 0",
                color: "#0f172a",
                fontSize: "1.1rem",
              }}
            >
              Answer
            </h3>
            <p
              style={{
                margin: 0,
                lineHeight: "1.6",
                color: "#334155",
                whiteSpace: "pre-wrap",
              }}
            >
              {result.answer}
            </p>
          </div>

          {/* Retrieved Matches Citations */}
          {result.matches && result.matches.length > 0 && (
            <div>
              <h4
                style={{
                  margin: "0 0 0.75rem 0",
                  color: "#475569",
                  fontSize: "1rem",
                }}
              >
                Retrieved Sources ({result.matches.length})
              </h4>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                {result.matches.map((match, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: "12px",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                      backgroundColor: "#ffffff",
                      fontSize: "0.9rem",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontWeight: "600",
                        marginBottom: "6px",
                        color: "#475569",
                      }}
                    >
                      <span>
                        📄 {match.metadata?.filename || `Source #${idx + 1}`}
                      </span>
                      {match.score !== undefined && (
                        <span
                          style={{
                            color: "#059669",
                            background: "#ecfdf5",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            fontSize: "0.8rem",
                          }}
                        >
                          Similarity: {(match.score * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <p
                      style={{
                        margin: 0,
                        color: "#64748b",
                        fontSize: "0.85rem",
                      }}
                    >
                      {match.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Collapsible Debug Context */}
          <div>
            <button
              type="button"
              onClick={() => setShowDebug(!showDebug)}
              style={{
                background: "none",
                border: "none",
                color: "#2563eb",
                cursor: "pointer",
                padding: 0,
                fontSize: "0.9rem",
                fontWeight: "500",
              }}
            >
              {showDebug
                ? "▼ Hide Generated Context Block for LLM"
                : "▶ Show Generated Context Block for LLM"}
            </button>

            {showDebug && (
              <pre
                style={{
                  marginTop: "8px",
                  padding: "12px",
                  backgroundColor: "#1e293b",
                  color: "#f8fafc",
                  borderRadius: "8px",
                  overflowX: "auto",
                  fontSize: "0.8rem",
                  lineHeight: "1.5",
                }}
              >
                {result.generated_context}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
