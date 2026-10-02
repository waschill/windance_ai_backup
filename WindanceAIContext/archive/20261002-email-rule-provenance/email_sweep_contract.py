"""Content-free structural validation for bounded sweep receipts."""
def validate(result):
    required={'rules','checked','deleted','kept','notices','errors'}
    if type(result) is not dict or not required<=set(result) or set(result)-required-{'status','coverage','effects','accounting_reconciled'}:raise ValueError('Invalid sweep receipt')
    if any(type(result[k]) is not int or result[k]<0 for k in ('rules','checked','deleted','kept')):raise ValueError('Invalid sweep counts')
    if result['deleted']+result['kept']!=result['checked']:raise ValueError('Inconsistent sweep counts')
    if any(type(result[k]) is not list or any(type(v) is not str for v in result[k]) for k in ('notices','errors')):raise ValueError('Invalid sweep details')
    if result.get('status') not in (None,'held','partial'):raise ValueError('Invalid sweep status')
    coverage=result.get('coverage')
    if result.get('status')=='partial' and coverage is None:raise ValueError('Partial coverage missing')
    if coverage is not None:
        if type(coverage) is not dict or set(coverage)!={'version','rules_visited','rules_total','message_cap','has_more','cursor_advanced'}:raise ValueError('Invalid sweep coverage')
        if any(type(coverage[k]) is not int for k in ('version','rules_visited','rules_total','message_cap')):raise ValueError('Invalid coverage counts')
        if coverage['version']!=1 or coverage['message_cap']!=20 or not 0<=coverage['rules_visited']<=min(8,result['rules']) or coverage['rules_total']!=result['rules'] or result['checked']>20:raise ValueError('Invalid coverage bounds')
        if any(type(coverage[k]) is not bool for k in ('has_more','cursor_advanced')):raise ValueError('Invalid coverage flags')
        if coverage['has_more']!=(result.get('status')=='partial'):raise ValueError('Partial state mismatch')
    effects=result.get('effects')
    if effects is not None:
        if type(effects) is not dict or set(effects)!={'newly_confirmed','previously_confirmed'} or any(type(v) is not int or v<0 for v in effects.values()) or sum(effects.values())!=result['deleted']:raise ValueError('Invalid effect counts')
    if 'accounting_reconciled' in result and (type(result['accounting_reconciled']) is not int or not 0<=result['accounting_reconciled']<=20):raise ValueError('Invalid accounting count')
    return result
