#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from opportunity_owner_notification import notify_owner, split_markdown


def main():
    body = '<!-- radar:test -->\n| Segnalazione | Documenti | Termine |\n|---|---|---|\n' + '\n'.join(f'| Segnalazione {n} àè | [Documento](<https://example.test/avviso-{n}.pdf>) | 2026-10-23 |' for n in range(2200))
    pieces = split_markdown(body)
    assert len(pieces)>2 and ''.join(pieces)==body
    assert all(len(p.encode('utf-8'))<=48000 for p in pieces)
    huge_line='à🙂'*40000
    assert ''.join(split_markdown(huge_line))==huge_line
    state={'issue':None,'comments':[],'created':0,'fail':True}
    def gh(args):
        command=args[:2]
        if command==['issue','list']:
            return json.dumps([state['issue']] if state['issue'] else [])
        if command==['issue','create']:
            text=Path(args[args.index('--body-file')+1]).read_text()
            assert len(text.encode('utf-8'))<50000
            state['created']+=1;state['issue']={'url':'https://github.com/example/repo/issues/1','body':text}
            return state['issue']['url']
        if command==['issue','view']:
            return json.dumps({'comments':state['comments']})
        if command==['issue','comment']:
            if len(state['comments'])==1 and state['fail']:
                state['fail']=False
                raise subprocess.CalledProcessError(1,args)
            text=Path(args[args.index('--body-file')+1]).read_text()
            assert len(text.encode('utf-8'))<50000
            state['comments'].append({'body':text});return ''
        raise AssertionError(args)
    kwargs=dict(repo='example/repo',marker='radar:test',title='Radar',body=body,assignee='example',gh=gh)
    try:
        notify_owner(**kwargs)
        raise AssertionError('Failure must propagate')
    except subprocess.CalledProcessError:
        pass
    notify_owner(**kwargs)
    notify_owner(**kwargs)
    assert state['created']==1 and len(state['comments'])==len(pieces)-1
    assert all('| Segnalazione | Documenti | Termine |' in c['body'] for c in state['comments'])
    rendered=state['issue']['body']+'\n'.join(c['body'] for c in state['comments'])
    for n in range(2200):
        assert rendered.count(f'https://example.test/avviso-{n}.pdf')==1
    print('Notifica Radar: rapporto completo, Unicode, limiti e ripresa senza duplicati PASS')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
