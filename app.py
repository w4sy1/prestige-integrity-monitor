from pathlib import Path
import shutil
import sys
import uuid
import re
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
    result={'schema_version':1,'root':str(root),'created_utc':now(),'files':rows,'options':{'extended':extended}}
    result['incomplete_files']=incomplete(result);result['ok']=not result['incomplete_files']
    return result


def validate(snapshot):
    if not isinstance(snapshot,dict) or snapshot.get('schema_version')!=1 or not isinstance(snapshot.get('root'),str) or not isinstance(snapshot.get('files'),dict):
        raise ValueError('Nieprawidłowy baseline.')
    if not isinstance(snapshot.get('options',{}),dict):raise ValueError('Nieprawidłowe opcje baseline.')
    if 'extended' in snapshot.get('options',{}) and type(snapshot['options']['extended']) is not bool:raise ValueError('Nieprawidłowy tryb baseline.')
    for name,row in snapshot['files'].items():
        if not isinstance(name,str) or not isinstance(row,dict):raise ValueError('Nieprawidłowy wpis baseline.')
        inside(snapshot['root'],name)
        if type(row.get('size')) is not int or row['size']<0 or type(row.get('mtime_ns')) is not int or not re.fullmatch('[a-fA-F0-9]{64}',str(row.get('sha256',''))):
            raise ValueError('Nieprawidłowe metadane pliku baseline.')
    return snapshot


def incomplete(snapshot):
    if not snapshot.get('options',{}).get('extended'):return []
    result=[]
    for name,row in snapshot['files'].items():
        metadata=row.get('extended') or {}
        if (not isinstance(metadata,dict) or metadata.get('acl_status') not in ('OK','POSIX_MODE_ONLY')
                or metadata.get('ads_status') not in ('OK','NOT_APPLICABLE')):
            result.append(name);continue
        streams=metadata.get('streams',[])
        if not isinstance(streams,list) or any(not isinstance(stream,dict) or not re.fullmatch('[a-fA-F0-9]{64}',str(stream.get('sha256',''))) for stream in streams):
            result.append(name)
    return result

def compare(before,after):
    validate(before);validate(after)
    if before.get('schema_version')!=1 or before.get('root')!=after.get('root'):raise ValueError('Nieprawidłowy baseline lub inny root.')
    a=before['files'];b=after['files'];result={'NEW':[],'MODIFIED':[],'DELETED':[],'UNCHANGED':[]}
    for path in sorted(a.keys()|b.keys()):
        inside(after['root'],path)
        status='NEW' if path not in a else 'DELETED' if path not in b else 'UNCHANGED' if a[path]==b[path] else 'MODIFIED'
        result[status].append(path)
    unknown=sorted(set(incomplete(before))|set(incomplete(after)))
    return {**result,'INCOMPLETE':unknown,'ok':not(result['NEW'] or result['MODIFIED'] or result['DELETED'] or unknown)}

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
    if previous is not None:validate(previous)
    current=capture(root,a.extended or bool(previous and previous.get('options',{}).get('extended')))
    if a.command=='baseline':
        if baseline.exists():raise FileExistsError(baseline)
        if not current['ok']:return {'created':False,'ok':False,'incomplete_files':current['incomplete_files']}
        atomic_json(baseline,current);return current
    delta=compare(previous,current)
    if a.command=='check':return delta
    if a.command=='update':
        if not a.accept_changes:return {'plan':'Aktualizacja wymaga --accept-changes','changes':delta}
        if not current['ok']:return {'updated':False,'ok':False,'incomplete_files':current['incomplete_files']}
        backup=baseline.with_name(baseline.name+'.'+uuid.uuid4().hex+'.bak');shutil.copy2(baseline,backup)
        atomic_json(baseline,current);return {'updated':True,'previous_baseline':str(backup),'changes':delta}
    raise ValueError('Wybierz polecenie.')

if __name__=='__main__':sys.exit(entry(build,handle))
