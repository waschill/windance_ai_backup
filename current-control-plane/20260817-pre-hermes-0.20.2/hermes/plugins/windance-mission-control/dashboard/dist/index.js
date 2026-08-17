(function () {
  "use strict";
  const SDK = window.__HERMES_PLUGIN_SDK__;
  const registry = window.__HERMES_PLUGINS__;
  if (!SDK || !registry) return;

  const h = SDK.React.createElement;
  const { useState, useEffect, useCallback } = SDK.hooks;
  const { Card, CardHeader, CardTitle, CardContent, Badge, Button } = SDK.components;
  const failedStatuses = new Set(["blocked", "failed"]);
  const API = "/api/plugins/windance-mission-control/tasks";

  function MissionControlPage() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(function () {
      setLoading(true);
      setError(null);
      SDK.fetchJSON(API)
        .then(function (response) { setTasks(response.tasks || []); })
        .catch(function (reason) { setError(String(reason)); })
        .finally(function () { setLoading(false); });
    }, []);

    useEffect(function () { load(); }, [load]);

    return h("div", { className: "wmc-page" },
      h("div", { className: "wmc-head" },
        h("div", null,
          h("h1", { className: "wmc-title" }, "Windance Mission Control"),
          h("p", { className: "wmc-muted" }, "Active work first, followed by recent outcomes from the local Harness.")),
        h(Button, { onClick: load, disabled: loading, "aria-label": "Refresh Mission Control" }, loading ? "Loading…" : "Refresh")),
      error && h("div", { role: "alert", className: "wmc-error" }, error),
      !loading && !error && !tasks.length && h("p", { className: "wmc-muted" }, "No active or recent staff work is available."),
      h("div", { className: "wmc-grid" }, tasks.map(function (task) {
        const failed = failedStatuses.has(task.status);
        return h(Card, { key: task.id, className: failed ? "wmc-danger" : "" },
          h(CardHeader, null,
            h("div", { className: "wmc-row" },
              h(CardTitle, null, task.title),
              h("div", { className: "wmc-meta" },
                h(Badge, { tone: task.is_complete ? "success" : failed ? "warning" : "secondary" }, task.status.replaceAll("_", " ")),
                task.is_escalation && h(Badge, { tone: "warning" }, "Escalation"))),
            h("div", { className: "wmc-meta" },
              h("span", null, "Assignee: ", task.assignee),
              task.target_host && h("span", null, task.target_host),
              h("time", { dateTime: task.updated_at }, "Updated ", new Date(task.updated_at).toLocaleString()),
              h("span", null, task.id))),
          h(CardContent, { className: "wmc-content" },
            h("section", null,
              h("h2", { className: "wmc-label" }, "Last progress"),
              h("p", { className: "wmc-copy" }, task.last_progress || "No progress recorded.")),
            h("section", null,
              h("h2", { className: "wmc-label" }, "Verification evidence"),
              h("p", { className: "wmc-copy" }, task.verification_evidence || "No verification evidence recorded.")),
            task.blocker && h("section", { className: "wmc-danger wmc-wide" },
              h("h2", { className: "wmc-label" }, "Blocker / failure"),
              h("p", { className: "wmc-copy" }, task.blocker))));
      })));
  }

  registry.register("windance-mission-control", MissionControlPage);
})();
