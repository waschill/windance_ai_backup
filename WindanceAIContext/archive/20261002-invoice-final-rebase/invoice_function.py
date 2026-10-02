def odoo_unpaid_customer_invoices(question: str = "", limit: int = 200) -> tuple[str, str, str]:
    """Read posted unpaid invoices; keep amounts in their original currencies."""
    from decimal import Decimal, InvalidOperation

    failure = ("I could not verify unpaid invoices from Odoo; no invoice report was produced.",
               "odoo-error", "odoo-unpaid-invoices")
    try:
        cap = max(1, min(int(limit), 1000))
        rows = odoo_execute_kw(
            "account.move", "search_read",
            [[['move_type', '=', 'out_invoice'], ['state', '=', 'posted'],
              ['payment_state', 'in', ['not_paid', 'partial']], ['amount_residual', '>', 0]]],
            {"fields": ["id", "name", "partner_id", "invoice_date", "invoice_date_due",
                        "amount_total", "amount_residual", "currency_id", "payment_state"],
             "limit": cap, "order": "invoice_date_due asc, invoice_date asc, name asc"},
        )
    except Exception:
        # Remote errors may contain private payloads. Do not turn one into a report.
        return failure
    if not isinstance(rows, list):
        return failure
    scope = ('Scope: posted customer invoices marked Not Paid or Partially Paid with a positive remaining balance. '
             'In Payment invoices are excluded; this report does not verify bank settlement or authorize collection messages.')
    if not rows:
        return ("I checked Odoo Accounting and found no posted customer invoices marked Not Paid or Partially Paid with a positive remaining balance.\n\n" + scope,
                "deterministic", "odoo-unpaid-invoices")

    totals = {}
    currencies = {}
    customers = set()
    invoices = []
    seen = set()
    try:
        for row in rows:
            invoice_id = row['id']
            partner = row['partner_id']
            currency = row['currency_id']
            if (not isinstance(invoice_id, int) or isinstance(invoice_id, bool) or invoice_id <= 0
                    or invoice_id in seen or not isinstance(partner, list) or len(partner) < 2
                    or not isinstance(currency, list) or len(currency) < 2
                    or not partner[0] or not currency[0] or not str(currency[1]).strip()):
                return failure
            if row.get('payment_state') not in ('not_paid', 'partial'):
                return failure
            residual = Decimal(str(row['amount_residual']))
            original = Decimal(str(row['amount_total']))
            if not residual.is_finite() or not original.is_finite() or residual <= 0 or original < 0:
                return failure
            currency_id, currency_name = currency[0], str(currency[1]).strip()
            if currency_id in currencies and currencies[currency_id] != currency_name:
                return failure
            currencies[currency_id] = currency_name
            totals[currency_id] = totals.get(currency_id, Decimal('0')) + residual
            customers.add(partner[0])
            seen.add(invoice_id)
            due = row.get('invoice_date_due')
            if due:
                due_date = dt.date.fromisoformat(str(due))
                due_text = f'{due_date.month}/{due_date.day}/{due_date.year}'
            else:
                due_text = 'no due date'
            invoices.append((str(partner[1]) or 'Unknown customer', currency_id,
                             str(row.get('name') or f'Odoo #{invoice_id}'), due_text,
                             original, residual, str(due or '9999-12-31'), invoice_id))
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return failure

    def money(amount, currency_id):
        # Preserve returned fractional precision instead of silently rounding a
        # three-decimal currency to cents. Always show at least two places.
        places = max(2, -amount.as_tuple().exponent)
        return f'{currencies[currency_id]} {amount:,.{places}f}'

    totals_text = '; '.join(money(totals[k], k)
                            for k in sorted(totals, key=lambda k: (currencies[k], str(k))))
    customer_word = 'customer' if len(customers) == 1 else 'customers'
    invoice_word = 'invoice' if len(invoices) == 1 else 'invoices'
    lines = [f'Odoo invoices marked Not Paid or Partially Paid: {len(customers)} {customer_word}, '
             f'{len(invoices)} {invoice_word}. Remaining balances by currency: {totals_text}.', '']
    for customer, currency_id, name, due, original, residual, _, _id in sorted(
            invoices, key=lambda x: (x[6], x[0], x[2], x[7])):
        lines.append(f'- {customer}: Invoice {name}, Invoice Total: {money(original, currency_id)}, '
                     f'Remaining: {money(residual, currency_id)}, Due {due}')
    if len(rows) >= cap:
        lines += ['', f'Note: this result hit the {cap}-invoice read limit; '
                  'there may be more unpaid invoices. These totals cover only the displayed records.']
    lines += ['', scope]
    return '\n'.join(lines), 'deterministic', 'odoo-unpaid-invoices'
