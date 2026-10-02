"""Trusted worker exchange counter, including OAuth; not an OS sandbox."""
from contextlib import contextmanager
from threading import Lock
_scope_lock=Lock()
_active=None
class BudgetExhausted(RuntimeError):pass
class Budget:
    def __init__(self,limit):
        self.limit=limit;self.used=0;self.lock=Lock()
    def charge(self):
        with self.lock:
            if self.used>=self.limit:raise BudgetExhausted('Mailbox exchange budget exhausted; reconcile prior outcomes')
            self.used+=1
@contextmanager
def exchange_budget(limit=256):
    global _active
    if type(limit) is not int or not 1<=limit<=256:raise ValueError('Invalid mailbox exchange budget')
    with _scope_lock:
        if _active is not None:raise ValueError('Nested mailbox exchange budget refused')
        budget=Budget(limit);_active=budget
    try:yield budget
    finally:
        with _scope_lock:_active=None
def charge_exchange():
    with _scope_lock:budget=_active
    if budget is not None:budget.charge()
