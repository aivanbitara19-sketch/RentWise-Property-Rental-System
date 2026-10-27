"""Restore a database backup after stopping the application. Usage: python scripts/restore.py backups/file.db"""
import os,sys,sqlite3,shutil
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv)!=2: raise SystemExit('Usage: python scripts/restore.py path/to/backup.db')
source=os.path.abspath(sys.argv[1]); target=os.environ.get('PROPERTY_DB',os.path.join(base,'property_rental.db'))
if not os.path.isfile(source): raise SystemExit('Backup file not found')
with sqlite3.connect(source) as c:
    if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise SystemExit('Backup failed integrity check; restore aborted')
if os.path.exists(target): shutil.copy2(target,target+'.pre-restore.bak')
shutil.copy2(source,target)
with sqlite3.connect(target) as c:
    if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise SystemExit('Restored database integrity check failed')
print('Restore complete and integrity verified:',target)
