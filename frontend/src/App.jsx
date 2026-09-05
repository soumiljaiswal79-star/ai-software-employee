import { useState } from "react";
import "./App.css";

function App() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runTask = async () => {
    if (!task.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/task", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: task.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Task failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="brand">
            <span className="brand-icon">AI</span>
            <span>AI Software Employee</span>
          </div>

          <p className="subtitle">
            Autonomous coding assistant that plans, edits, tests and verifies.
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Online
        </div>
      </header>

      <main className="container">
        <section className="task-card">
          <div className="section-title">
            <h2>Give your employee a task</h2>
            <span>AI Developer</span>
          </div>

          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Example: Add a divide function to calculator.py and create tests for it."
            rows={5}
          />

          <div className="task-footer">
            <span className="hint">
              The employee will inspect → modify → test → fix → verify.
            </span>

            <button
              onClick={runTask}
              disabled={loading || !task.trim()}
            >
              {loading ? "Working..." : "Run Task"}
            </button>
          </div>
        </section>

        {loading && (
          <section className="progress-card">
            <div className="loading-spinner"></div>

            <div>
              <h3>AI employee is working...</h3>
              <p>
                Inspecting files, making changes and running tests.
              </p>
            </div>
          </section>
        )}

        {error && (
          <section className="error-card">
            <strong>Task failed</strong>
            <p>{error}</p>
          </section>
        )}

        {result && !loading && (
          <>
            <section className="overview-grid">
              <div className="metric-card">
                <span>Status</span>
                <strong className={result.status === "completed" ? "success" : "warning"}>
                  {result.status}
                </strong>
              </div>

              <div className="metric-card">
                <span>Iterations</span>
                <strong>
                  {result.iterations} / {result.maximum_iterations}
                </strong>
              </div>

              <div className="metric-card">
                <span>Files Modified</span>
                <strong>
                  {result.files_modified?.length || 0}
                </strong>
              </div>

              <div className="metric-card">
                <span>Tests Run</span>
                <strong>
                  {result.test_results?.length || 0}
                </strong>
              </div>
            </section>

            <section className="result-card">
              <div className="card-header">
                <h2>Execution Plan</h2>
              </div>

              <div className="plan">
                {result.plan?.map((step, index) => (
                  <div className="plan-step" key={index}>
                    <div className="step-number">{index + 1}</div>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </section>

            <div className="two-column">
              <section className="result-card">
                <div className="card-header">
                  <h2>Files Modified</h2>
                </div>

                {result.files_modified?.length ? (
                  <ul className="file-list">
                    {result.files_modified.map((file) => (
                      <li key={file}>
                        <span className="file-icon">▣</span>
                        {file}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty">No files modified.</p>
                )}
              </section>

              <section className="result-card">
                <div className="card-header">
                  <h2>Verification</h2>
                </div>

                {result.test_results?.length ? (
                  <div className="tests">
                    {result.test_results.map((test, index) => (
                      <div className="test-row" key={index}>
                        <span
                          className={
                            test.status === "passed"
                              ? "test-icon passed"
                              : "test-icon failed"
                          }
                        >
                          {test.status === "passed" ? "✓" : "✕"}
                        </span>

                        <div>
                          <strong>{test.status}</strong>
                          <small>{test.command}</small>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty">No tests recorded.</p>
                )}
              </section>
            </div>

            <section className="result-card">
              <div className="card-header">
                <h2>AI Report</h2>
              </div>

              <div className="report">
                {result.response || result.final_message || "Task completed."}
              </div>
            </section>

            {result.tools_used?.length > 0 && (
              <section className="result-card">
                <div className="card-header">
                  <h2>Activity</h2>
                  <span>{result.tools_used.length} actions</span>
                </div>

                <div className="activity">
                  {result.tools_used.map((tool, index) => (
                    <div className="activity-row" key={index}>
                      <span className="activity-action">
                        {tool.action}
                      </span>

                      <strong>{tool.tool}</strong>

                      <span
                        className={
                          tool.result_status === "passed" ||
                          tool.result_status === "success"
                            ? "success"
                            : tool.result_status === "failed"
                              ? "danger"
                              : ""
                        }
                      >
                        {tool.result_status}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;