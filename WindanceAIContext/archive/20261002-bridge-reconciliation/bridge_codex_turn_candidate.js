function codexTurn({ threadId, message, user, requestId }) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(codexUrl);
    const pending = new Map();
    const earlyCompletions = new Map();
    let nextId = 1, text = '', lastMessage = '';
    let settled = false, activeTurnId = null, turnPosted = false;
    let stopReason = null, stopTimer = null, interruptSent = false;
    const timeout = setTimeout(() => { requestStop('deadline').catch(() => {}); }, 600000);

    function failure(message, code) {
      const error = new Error(message); error.code = code; return error;
    }
    function finish(error, result, terminalConfirmed = false) {
      if (settled) return;
      // Transport failure is not evidence that an accepted turn stopped.
      if (error && turnPosted && !terminalConfirmed) error.code = 'EXECUTION_UNCERTAIN';
      settled = true;
      clearTimeout(timeout); if (stopTimer) clearTimeout(stopTimer);
      if (requestId) abortHandlers.delete(requestId);
      for (const p of pending.values()) {
        clearTimeout(p.timer); p.reject(failure('Connection settled', 'CONNECTION_SETTLED'));
      }
      pending.clear();
      try { ws.close(); } catch {}
      error ? reject(error) : resolve(result);
    }
    function request(method, params = {}) {
      if (settled) return Promise.reject(failure('Connection settled', 'CONNECTION_SETTLED'));
      const id = nextId++;
      return new Promise((resolveRequest, rejectRequest) => {
        const timer = setTimeout(() => {
          pending.delete(id); rejectRequest(new Error(`Timed out waiting for ${method}`));
        }, 30000);
        pending.set(id, { resolve: resolveRequest, reject: rejectRequest, timer, method });
        try { ws.send(JSON.stringify({ method, id, params })); }
        catch (error) { pending.delete(id); clearTimeout(timer); rejectRequest(error); }
      });
    }
    async function requestStop(reason) {
      if (settled) return;
      if (!stopReason) {
        stopReason = reason;
        stopTimer = setTimeout(() => finish(failure('Interruption not confirmed',
          turnPosted ? 'EXECUTION_UNCERTAIN' : 'INTERRUPTED')), 45000);
        if (requestId) {
          state.tasks[requestId].interrupt_requested = reason;
          try { persist(); } catch (error) { finish(error); throw error; }
        }
      }
      if (activeTurnId && !interruptSent) {
        interruptSent = true;
        try { await request('turn/interrupt', { threadId, turnId: activeTurnId }); }
        catch (error) { finish(error); throw error; }
      }
      // Await the turn/completed event; an RPC acknowledgment is insufficient.
    }
    if (requestId) abortHandlers.set(requestId, () => requestStop('owner'));

    function completed(turn) {
      if (!activeTurnId || turn.id !== activeTurnId) return;
      if (turn.status === 'completed') finish(null, { threadId, text: text || lastMessage, turnId: turn.id, stopRequested: stopReason });
      else if (['failed', 'interrupted'].includes(turn.status)) {
        finish(failure(turn.error?.message || `Codex turn ended as ${turn.status}`,
          turn.status === 'interrupted' ? 'INTERRUPTED' : 'REMOTE_FAILED'), null, true);
      }
    }

    ws.addEventListener('message', async (event) => {
      if (settled) return;
      let m;
      try { m = JSON.parse(event.data); } catch (error) { finish(error); return; }
      if (m.id && pending.has(m.id)) {
        const p = pending.get(m.id); pending.delete(m.id); clearTimeout(p.timer);
        m.error ? p.reject(new Error(`${p.method}: ${m.error.message}`)) : p.resolve(m.result);
        return;
      }
      if (m.params?.threadId && threadId && m.params.threadId !== threadId) return;
      if (m.method === 'item/completed' && m.params?.item?.type === 'agentMessage') {
        lastMessage = m.params.item.text || '';
        if (m.params.item.phase === 'final_answer') text = lastMessage;
      }
      if (m.method === 'turn/completed') {
        const turn = m.params?.turn || {};
        if (!activeTurnId && turnPosted && turn.id && m.params?.threadId === threadId) {
          if (earlyCompletions.size >= 8) { finish(new Error('Unmatched completion buffer exceeded')); return; }
          earlyCompletions.set(turn.id, turn);
        } else {
          completed(turn);
        }
      }
    });
    ws.addEventListener('error', () => finish(new Error('Codex App Server connection failed')));
    ws.addEventListener('close', () => { if (!settled) finish(new Error('Connection closed before terminal evidence')); });
    ws.addEventListener('open', async () => {
      try {
        await request('initialize', { clientInfo: { name: 'windance_codex_bridge', title: 'Windance Codex Bridge', version: '1.0' } });
        if (settled) return;
        ws.send(JSON.stringify({ method: 'initialized', params: {} }));
        let actualThreadId = threadId;
        if (actualThreadId) await request('thread/resume', { threadId: actualThreadId });
        else {
          const started = await request('thread/start', { model: 'gpt-5.6-terra', cwd: workdir, approvalPolicy: 'never', sandbox: 'danger-full-access', personality: 'friendly', serviceName: 'windance-vega' });
          actualThreadId = started.thread.id;
        }
        if (settled) return;
        threadId = actualThreadId;
        if (requestId) { state.tasks[requestId].acceptance_receipt = { thread_id: threadId }; persist(); }
        if (stopReason) { finish(failure('Interrupted before turn start', 'INTERRUPTED')); return; }
        // Persist uncertainty before transport: crash here must never imply no execution.
        turnPosted = true;
        if (requestId) { state.tasks[requestId].execution_phase = 'turn_start_submitted'; persist(); }
        const turn = await request('turn/start', {
          threadId: actualThreadId,
          input: [{ type: 'text', text: `${windanceExecutiveContext}\n\nWilliam's request: ${message}` }],
          cwd: workdir, approvalPolicy: 'never', sandboxPolicy: { type: 'dangerFullAccess' },
          model: 'gpt-5.6-terra', effort: 'medium', summary: 'concise', personality: 'pragmatic',
        });
        if (settled) return;
        activeTurnId = turn.turn?.id;
        if (!activeTurnId) throw new Error('Turn start returned no durable turn identity');
        if (requestId) {
          const task = state.tasks[requestId];
          task.acceptance_receipt = { thread_id: threadId, turn_id: activeTurnId };
          state.threads[`${task.requested_by.toLowerCase()}:manager-v2:${task.session}`] = threadId;
          persist();
        }
        if (earlyCompletions.has(activeTurnId)) completed(earlyCompletions.get(activeTurnId));
        earlyCompletions.clear();
        if (settled) return;
        if (turn.turn.status === 'failed') finish(failure(turn.turn.error?.message || 'Codex refused the turn', 'REMOTE_FAILED'), null, true);
        else if (stopReason) await requestStop(stopReason);
      } catch (error) { finish(error); }
    });
  });
}
