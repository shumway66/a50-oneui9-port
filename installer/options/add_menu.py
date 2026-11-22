import os,sys
f=os.path.expanduser('~/Documents/updater-script'); s=open(f).read()
menu=open(sys.argv[1]).read(); save=open(sys.argv[2]).read()
if 'ur_ask' in s: sys.exit('menu already present - nothing changed')
a='ui_print "[1/5] Preparing partitions"'; b='ui_print "[5/5] Cleaning caches and temporary files"'
assert a in s and b in s, 'anchor lines not found'
s=s.replace(a, menu+a,1).replace(b, b+'\n'+save,1)
open(f+'.before_menu','w').write(open(f).read()); open(f,'w').write(s); print('menu added (backup: updater-script.before_menu)')
