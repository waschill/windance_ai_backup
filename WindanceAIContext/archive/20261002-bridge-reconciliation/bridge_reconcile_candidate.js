function readRetainedThread(threadId) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(codexUrl); let done = false, nextId = 1;
    const pending = new Map();
    const timeout = setTimeout(() => finish(new Error('Retained thread read timed out')), 15000);
    function finish(error, value) {
      if (done) return; done = true; clearTimeout(timeout);
      for (const p of pending.values()) p.reject(new Error('Read connection settled'));
      pending.clear(); try { ws.close(); } catch {}
      error ? reject(error) : resolve(value);
    }
    function rpc(method, params) {
      const id = nextId++;
      return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        try { ws.send(JSON.stringify({ id, method, params })); }
        catch (error) { pending.delete(id); reject(error); }
      });
    }
    ws.addEventListener('message', event => {
      if (done) return;
      try {
        const m = JSON.parse(event.data), p = pending.get(m.id);
        if (p) { pending.delete(m.id); m.error ? p.reject(new Error('Retained thread read rejected')) : p.resolve(m.result); }
      } catch (error) { finish(error); }
    });
    ws.addEventListener('error', () => finish(new Error('Retained thread connection failed')));
    ws.addEventListener('close', () => { if (!done) finish(new Error('Retained thread connection closed')); });
    ws.addEventListener('open', async () => {
      try {
        await rpc('initialize', { clientInfo: { name: 'windance_codex_reconcile', title: 'Windance execution reconciliation', version: '1' } });
        if (done) return;
        ws.send(JSON.stringify({ method: 'initialized', params: {} }));
        const result = await rpc('thread/read', { threadId, includeTurns: true });
        finish(null, result.thread);
      } catch (error) { finish(error); }
    });
  });
}

function retainedOutcome(task, thread) {
  const receipt = task.acceptance_receipt;
  if (!receipt?.thread_id || !receipt?.turn_id) return null;
  if (thread?.id !== receipt.thread_id || !['idle', 'notLoaded'].includes(thread.status?.type)) return null;
  const matches = Array.isArray(thread.turns) ? thread.turns.filter(t => t.id === receipt.turn_id) : [];
  if (matches.length !== 1) return null;
  const turn = matches[0];
  if (!['completed', 'failed', 'interrupted'].includes(turn.status)) return null;
  const final = (turn.items || []).filter(i => i.type === 'agentMessage' && i.phase === 'final_answer').at(-1)?.text;
  if (turn.status === 'completed' && (typeof final !== 'string' || !final.trim())) return null;
  return { current_status: turn.status, result_summary: turn.status === 'completed' ? final : null,
    error_message: turn.status === 'completed' ? null : 'Retained turn ended without successful completion; accepted side effects require separate verification.',
    verification_evidence: { thread_id: receipt.thread_id, turn_id: receipt.turn_id, source: 'thread/read', terminal_status: turn.status } };
}

const reconcilingJobs = new Set();
async function reconcileJob(task) {
  if (task.current_status !== 'execution_uncertain' || reconcilingJobs.has(task.task_id)) return;
  const receipt = task.acceptance_receipt;
  if (!receipt?.thread_id || !receipt?.turn_id) return;
  reconcilingJobs.add(task.task_id);
  try {
    const thread = await readRetainedThread(receipt.thread_id);
    if (task.current_status !== 'execution_uncertain' || task.acceptance_receipt !== receipt) return;
    const outcome = retainedOutcome(task, thread);
    if (!outcome) return;
    const before = { ...task };
    Object.assign(task, outcome, { updated_at: iso(), reconciled_at: iso() });
    try { persist(); } catch (error) {
      for (const key of Object.keys(task)) if (!(key in before)) delete task[key];
      Object.assign(task, before); throw error;
    }
  } catch {
    // Missing/unavailable evidence stays held; never replay or guess success.
  } finally { reconcilingJobs.delete(task.task_id); }
}

async function reconcileUncertain() {
  for (const task of Object.values(state.tasks).filter(t => t.manager_v2 && t.current_status === 'execution_uncertain')) {
    await reconcileJob(task);
  }
}
