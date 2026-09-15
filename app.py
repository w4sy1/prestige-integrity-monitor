from pathlib import Path
import shutil
import sys
import uuid
from runtime import atomic_json,digest,entry,files,inside,now,parser,read_json

def capture(root,extended=False):
    root=Path(root).resolve();rows={}
    for p in files(root):
        before=p.stat();sha=digest(p);after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Zmiana podczas odczytu.')
        rows[p.relative_to(root).as_posix()]={'size':before.st_size,'mtime_ns':before.st_mtime_ns,'sha256':sha}
    if extended:
        from extended import collect
        metadata=collect(root,rows)
        for name in rows:rows[name]['extended']=metadata.get(name,{'status':'UNKNOWN'})
    return {'schema_version':1,'root':str(root),'created_utc':now(),'files':rows,'options':{'extended':extended}}

def compare(before,after):
    if before.get('schema_version')!=1 or before.get('root')!=after.get('root'):raise ValueError('Nieprawidłowy baseline lub inny root.')
    a=before['files'];b=after['files'];result={'NEW':[],'MODIFIED':[],'DELETED':[],'UNCHANGED':[]}
    for path in sorted(a.keys()|b.keys()):
        inside(after['root'],path)
        status='NEW' if path not in a else 'DELETED' if path not in b else 'UNCHANGED' if a[path]==b[path] else 'MODIFIED'
        result[status].append(path)
    return {**result,'ok':not(result['NEW'] or result['MODIFIED'] or result['DELETED'])}

def build():
    p=parser('Integralność katalogu i potwierdzane aktualizacje baseline.')
    p.add_argument('command',nargs='?',choices=['keygen','sign','verify-signature','baseline','check','update']);p.add_argument('--root');p.add_argument('--baseline');p.add_argument('--accept-changes',action='store_true')
    p.add_argument('--extended',action='store_true',help='Uwzględnij ACL/ADS Windows lub POSIX mode')
    from signing import add_arguments
    add_arguments(p)
    return p

def handle(a):
    if a.command in ('keygen','sign','verify-signature'):
        from signing import handle as signing_handle
        return signing_handle(a,a.baseline)
    if not a.root or not a.baseline:raise ValueError('Wymagane root i baseline.')
    root=Path(a.root).resolve();baseline=Path(a.baseline)
    if baseline.is_symlink() or baseline.resolve().is_relative_to(root):raise ValueError('Baseline poza źródłem, bez symlinków.')
    previous=read_json(baseline) if a.command!='baseline' else None
    current=capture(root,a.extended or bool(previous and previous.get('options',{}).get('extended')))
    if a.command=='baseline':
        if baseline.exists():raise FileExistsError(baseline)
        atomic_json(baseline,current);return current
    delta=compare(previous,current)
    if a.command=='check':return delta
    if a.command=='update':
        if not a.accept_changes:return {'plan':'Aktualizacja wymaga --accept-changes','changes':delta}
        backup=baseline.with_name(baseline.name+'.'+uuid.uuid4().hex+'.bak');shutil.copy2(baseline,backup)
        atomic_json(baseline,current);return {'updated':True,'previous_baseline':str(backup),'changes':delta}
    raise ValueError('Wybierz polecenie.')

if __name__=='__main__':sys.exit(entry(build,handle))
