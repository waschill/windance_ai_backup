"""Validate one classifier batch before it can authorize mailbox actions."""
def validated_chunk(rows,expected):
    expected=set(expected)
    if not isinstance(rows,list) or len(rows)!=len(expected):return {}
    result={}
    for row in rows:
        if not isinstance(row,dict):return {}
        index=row.get('index')
        if type(index) is not int or index not in expected or index in result:return {}
        decision=row.get('decision');reason=row.get('reason');category=row.get('category','uncategorized');intent=row.get('draft_intent','')
        if not isinstance(decision,str) or decision.strip().lower() not in {'automatic','draft','escalate'}:return {}
        if not isinstance(reason,str) or not reason.strip() or not isinstance(category,str) or not isinstance(intent,str):return {}
        decision=decision.strip().lower()
        if decision=='draft' and not intent.strip():return {}
        result[index]={'decision':decision,'category':category[:120],'reason':reason[:500],'draft_intent':intent[:1200]}
    return result if set(result)==expected else {}
