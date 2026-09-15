"""Optional ACL and alternate-stream evidence, without modifying permissions."""
import os
from runtime import powershell


def collect(root,names):
    if os.name!='nt':
        from pathlib import Path
        return {name:{'mode':oct((Path(root)/name).stat().st_mode & 0o7777),'acl_status':'POSIX_MODE_ONLY','ads_status':'NOT_APPLICABLE'} for name in names}
    root=str(root).replace("'","''");result={}
    names=list(names)
    for start in range(0,len(names),100):
        quoted=','.join("'"+name.replace("'","''")+"'" for name in names[start:start+100])
        script=r'''$root='ROOT';$r=[ordered]@{}
foreach($relative in @(NAMES)){
 $file=Join-Path $root $relative;$row=[ordered]@{}
 try{$acl=Get-Acl -LiteralPath $file;$row.sddl=$acl.Sddl;$row.acl_status='OK'}catch{$row.acl_status='UNKNOWN'}
 try{
  $row.streams=@(Get-Item -LiteralPath $file -Stream * | Where-Object Stream -ne ':$DATA' | ForEach-Object {
   $hash=$null;try{$hash=(Get-FileHash -LiteralPath ($file+':'+$_.Stream) -Algorithm SHA256).Hash}catch{}
   [pscustomobject]@{name=$_.Stream;size=$_.Length;sha256=$hash}
  } | Sort-Object name);$row.ads_status='OK'
 }catch{$row.ads_status='UNKNOWN'}
 $r[$relative]=$row
};$r|ConvertTo-Json -Depth 6'''
        result.update(powershell(script.replace('ROOT',root).replace('NAMES',quoted),120))
    return result
