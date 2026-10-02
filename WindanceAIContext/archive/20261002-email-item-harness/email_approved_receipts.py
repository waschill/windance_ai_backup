"""Minimal approved-executor receipts; provider acceptance is not delivery."""
def normalize(item,response):
    action=item['action']
    if not isinstance(response,dict):raise ValueError('Missing action receipt')
    if action in {'gmail.save','gmail.reply_needed'}:
        flag='saved' if action=='gmail.save' else 'reply_needed'
        if response.get(flag) is not True or response.get('message_id')!=item.get('message_id') or response.get('gmail_changed') is not False:raise ValueError('Invalid tracking receipt')
        return {flag:True,'message_id':item['message_id'],'gmail_changed':False}
    if response.get('action')!=action or not isinstance(response.get('result'),dict):raise ValueError('Action receipt mismatch')
    result=response['result'];identity=result.get('id')
    if not isinstance(identity,str) or not identity.strip():raise ValueError('Missing resource identity')
    flags={'gmail.mark_read':'marked_read','gmail.archive':'archived','gmail.delete':'trashed','gmail.create_draft':'draft_created','gmail.send':'sent'}
    flag=flags.get(action)
    if flag is None or result.get(flag) is not True:raise ValueError('Unsupported or unconfirmed action')
    if action in {'gmail.mark_read','gmail.archive','gmail.delete'} and identity!=item.get('message_id'):raise ValueError('Message identity mismatch')
    receipt={flag:True,'id':identity}
    if action=='gmail.send' and item.get('draft_id'):
        if result.get('draft_id')!=item['draft_id']:raise ValueError('Draft identity mismatch')
        receipt['draft_id']=item['draft_id']
    return {'action':action,'result':receipt}
