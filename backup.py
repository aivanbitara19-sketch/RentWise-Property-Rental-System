"""Create a consistent SQLite backup using SQLite's online backup API."""
import os, sqlite3
from datetime import datetime
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=os.environ.get('PROPERTY_DB',os.path.join(base,'property_rental.db'))
outdir=os.path.join(base,'backups'); os.makedirs(outdir,exist_ok=True)
if not os.path.exists(src): raise SystemExit(f'Database not found: {src}')
target=os.path.join(outdir,'property_rental_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.db')
with sqlite3.connect(src) as source, sqlite3.connect(target) as dest: source.backup(dest)
with sqlite3.connect(target) as check:
    result=check.execute('PRAGMA integrity_check').fetchone()[0]
    if result!='ok': raise SystemExit('Backup integrity check failed: '+result)
print('Backup verified:',target)
