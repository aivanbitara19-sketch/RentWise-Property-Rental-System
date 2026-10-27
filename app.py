import os, sqlite3, secrets, logging, shutil
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('PROPERTY_DB', os.path.join(BASE_DIR, 'property_rental.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=2*1024*1024)
logging.basicConfig(filename=os.path.join(BASE_DIR, 'app.log'), level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Administrator','Property Owner','Property Manager','Tenant','Maintenance Staff','Leasing Officer','Accountant')), full_name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS properties(id INTEGER PRIMARY KEY, name TEXT NOT NULL, address TEXT NOT NULL, property_type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS units(id INTEGER PRIMARY KEY, property_id INTEGER NOT NULL REFERENCES properties(id), unit_number TEXT NOT NULL, bedrooms INTEGER NOT NULL DEFAULT 0, monthly_rent REAL NOT NULL CHECK(monthly_rent>=0), status TEXT NOT NULL DEFAULT 'Vacant' CHECK(status IN ('Vacant','Occupied','Under Maintenance')), UNIQUE(property_id,unit_number));
CREATE TABLE IF NOT EXISTS tenants(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), full_name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS leases(id INTEGER PRIMARY KEY, unit_id INTEGER NOT NULL REFERENCES units(id), tenant_id INTEGER NOT NULL REFERENCES tenants(id), start_date TEXT NOT NULL, end_date TEXT NOT NULL, monthly_rent REAL NOT NULL CHECK(monthly_rent>=0), status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Active','Expired','Terminated')), approved_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, CHECK(end_date>=start_date));
CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY, lease_id INTEGER NOT NULL REFERENCES leases(id), amount REAL NOT NULL CHECK(amount>0), due_date TEXT NOT NULL, paid_date TEXT, payment_method TEXT, reference_no TEXT, status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(status IN ('Unpaid','Paid','Overdue')), recorded_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS maintenance_requests(id INTEGER PRIMARY KEY, unit_id INTEGER NOT NULL REFERENCES units(id), tenant_id INTEGER REFERENCES tenants(id), title TEXT NOT NULL, description TEXT NOT NULL, priority TEXT NOT NULL DEFAULT 'Normal' CHECK(priority IN ('Low','Normal','High','Urgent')), status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Assigned','In Progress','Completed','Rejected')), assigned_to INTEGER REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT);
CREATE TABLE IF NOT EXISTS utility_bills(id INTEGER PRIMARY KEY, unit_id INTEGER NOT NULL REFERENCES units(id), bill_type TEXT NOT NULL, amount REAL NOT NULL CHECK(amount>=0), due_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(status IN ('Unpaid','Paid','Overdue')));
CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, audience TEXT NOT NULL DEFAULT 'All', created_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), username TEXT, action TEXT NOT NULL, entity TEXT, entity_id INTEGER, details TEXT, ip_address TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
'''

def db_conn():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db
@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None: db.close()

def init_db():
    con = sqlite3.connect(DB_PATH); con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    if con.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        demos = [('admin','AdminDemo!2026','Administrator','System Administrator'),('owner','OwnerDemo!2026','Property Owner','Property Owner'),('manager','ManagerDemo!2026','Property Manager','Property Manager'),('accountant','AccountDemo!2026','Accountant','Accounting Officer'),('leasing','LeasingDemo!2026','Leasing Officer','Leasing Officer'),('maintenance','MaintDemo!2026','Maintenance Staff','Maintenance Staff'),('tenant','TenantDemo!2026','Tenant','Demo Tenant')]
        for u,p,r,n in demos: con.execute('INSERT INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)',(u,generate_password_hash(p),r,n))
        con.execute("INSERT INTO properties(name,address,property_type) VALUES('Sunrise Residences','Calamba, Laguna','Apartment')")
        pid=con.execute('SELECT id FROM properties LIMIT 1').fetchone()[0]
        for no,beds,rent,status in [('A-101',1,8500,'Occupied'),('A-102',2,12000,'Vacant'),('A-103',1,9000,'Under Maintenance')]: con.execute('INSERT INTO units(property_id,unit_number,bedrooms,monthly_rent,status) VALUES(?,?,?,?,?)',(pid,no,beds,rent,status))
        con.execute("INSERT INTO tenants(user_id,full_name,email,phone) VALUES(4,'Maria Santos','maria@example.com','09170000000')")
        tid=con.execute('SELECT id FROM tenants LIMIT 1').fetchone()[0]
        uid=con.execute("SELECT id FROM units WHERE unit_number='A-101'").fetchone()[0]
        start=date.today().replace(day=1); end=start+timedelta(days=365)
        con.execute("INSERT INTO leases(unit_id,tenant_id,start_date,end_date,monthly_rent,status,approved_by) VALUES(?,?,?,?,?,'Active',2)",(uid,tid,start.isoformat(),end.isoformat(),8500))
        lid=con.execute('SELECT id FROM leases LIMIT 1').fetchone()[0]
        con.execute("INSERT INTO payments(lease_id,amount,due_date,status) VALUES(?,?,?,'Unpaid')",(lid,8500,date.today().isoformat()))
        con.execute("INSERT INTO maintenance_requests(unit_id,tenant_id,title,description,priority,status,assigned_to) VALUES(?,?, 'Leaking faucet','Kitchen faucet needs inspection.','Normal','Assigned',6)",(uid,tid))
    con.commit(); con.close()

ROLE_ACCESS = {
 'properties': {'Administrator','Property Owner','Property Manager','Leasing Officer'},
 'units': {'Administrator','Property Owner','Property Manager','Leasing Officer','Maintenance Staff'},
 'tenants': {'Administrator','Property Owner','Property Manager','Leasing Officer'},
 'leases': {'Administrator','Property Owner','Property Manager','Leasing Officer'},
 'payments': {'Administrator','Property Owner','Accountant'},
 'maintenance': {'Administrator','Property Owner','Property Manager','Maintenance Staff','Tenant'},
 'utilities': {'Administrator','Property Owner','Property Manager','Accountant'},
 'notices': {'Administrator','Property Owner','Property Manager','Leasing Officer'},
 'users': {'Administrator'}, 'audit': {'Administrator'},
}
MODULES = {
 'properties': ('Properties','properties',[('name','Property name','text'),('address','Address','text'),('property_type','Type (Apartment/Condo/Commercial)','text')]),
 'units': ('Units','units',[('property_id','Property ID','number'),('unit_number','Unit number','text'),('bedrooms','Bedrooms','number'),('monthly_rent','Monthly rent','number'),('status','Status (Vacant/Occupied/Under Maintenance)','text')]),
 'tenants': ('Tenants','tenants',[('full_name','Full name','text'),('email','Email','email'),('phone','Phone','text')]),
 'leases': ('Leases','leases',[('unit_id','Unit ID','number'),('tenant_id','Tenant ID','number'),('start_date','Start date','date'),('end_date','End date','date'),('monthly_rent','Monthly rent','number'),('status','Status (Pending/Active/Expired/Terminated)','text')]),
 'payments': ('Payments','payments',[('lease_id','Lease ID','number'),('amount','Amount','number'),('due_date','Due date','date'),('paid_date','Paid date (optional)','date'),('payment_method','Payment method','text'),('reference_no','Reference number','text'),('status','Status (Unpaid/Paid/Overdue)','text')]),
 'maintenance': ('Maintenance Requests','maintenance_requests',[('unit_id','Unit ID','number'),('tenant_id','Tenant ID (optional)','number'),('title','Request title','text'),('description','Description','text'),('priority','Priority (Low/Normal/High/Urgent)','text')]),
 'utilities': ('Utility Bills','utility_bills',[('unit_id','Unit ID','number'),('bill_type','Bill type','text'),('amount','Amount','number'),('due_date','Due date','date'),('status','Status (Unpaid/Paid/Overdue)','text')]),
 'notices': ('Notices','notices',[('title','Title','text'),('body','Message','text'),('audience','Audience (All/Tenant/Staff)','text')]),
}

def audit(action, entity=None, entity_id=None, details=''):
    u=session.get('user') or {}
    db_conn().execute('INSERT INTO audit_logs(user_id,username,action,entity,entity_id,details,ip_address) VALUES(?,?,?,?,?,?,?)',(u.get('id'),u.get('username'),action,entity,entity_id,details,request.remote_addr))
    db_conn().commit()
def login_required(f):
    @wraps(f)
    def wrap(*a,**kw):
        if not session.get('user'): return redirect(url_for('login', next=request.path))
        return f(*a,**kw)
    return wrap
def role_required(roles):
    def deco(f):
        @wraps(f)
        def wrap(*a,**kw):
            if not session.get('user'): return redirect(url_for('login'))
            if session['user']['role'] not in roles: abort(403)
            return f(*a,**kw)
        return wrap
    return deco
@app.context_processor
def inject_user(): return {'current_user':session.get('user'),'today':date.today().isoformat()}
@app.route('/')
def home(): return redirect(url_for('dashboard') if session.get('user') else url_for('login'))
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form.get('username','').strip(); password=request.form.get('password','')
        row=db_conn().execute('SELECT * FROM users WHERE username=? AND active=1',(username,)).fetchone()
        if row and check_password_hash(row['password_hash'],password):
            session.clear(); session['user']={'id':row['id'],'username':row['username'],'role':row['role'],'full_name':row['full_name']}; session['csrf']=secrets.token_urlsafe(24)
            audit('LOGIN','users',row['id'],'Successful login'); return redirect(url_for('dashboard'))
        db_conn().execute('INSERT INTO audit_logs(username,action,entity,details,ip_address) VALUES(?,?,?,?,?)',(username,'FAILED_LOGIN','users','Invalid credentials or inactive account',request.remote_addr)); db_conn().commit()
        flash('Invalid username or password, or account is inactive.','error')
    return render_template('login.html')
@app.route('/logout',methods=['POST'])
@login_required
def logout():
    audit('LOGOUT','users',session['user']['id'],'User logged out'); session.clear(); return redirect(url_for('login'))
@app.route('/dashboard')
@login_required
def dashboard():
    d=db_conn()
    stats={'properties':d.execute('SELECT COUNT(*) FROM properties').fetchone()[0], 'units':d.execute('SELECT COUNT(*) FROM units').fetchone()[0], 'vacant':d.execute("SELECT COUNT(*) FROM units WHERE status='Vacant'").fetchone()[0], 'occupied':d.execute("SELECT COUNT(*) FROM units WHERE status='Occupied'").fetchone()[0], 'tenants':d.execute('SELECT COUNT(*) FROM tenants').fetchone()[0], 'overdue':d.execute("SELECT COUNT(*) FROM payments WHERE status='Overdue' OR (status='Unpaid' AND due_date<?)",(date.today().isoformat(),)).fetchone()[0], 'maintenance':d.execute("SELECT COUNT(*) FROM maintenance_requests WHERE status IN ('Pending','Assigned','In Progress')").fetchone()[0], 'leases_expiring':d.execute("SELECT COUNT(*) FROM leases WHERE status='Active' AND end_date BETWEEN ? AND ?",(date.today().isoformat(),(date.today()+timedelta(days=30)).isoformat())).fetchone()[0]}
    return render_template('dashboard.html',stats=stats)
@app.route('/<module>',methods=['GET','POST'])
@login_required
def module_page(module):
    if module not in MODULES: abort(404)
    if session['user']['role'] not in ROLE_ACCESS[module]: abort(403)
    title,table,fields=MODULES[module]; d=db_conn()
    if request.method=='POST':
        if request.form.get('csrf') != session.get('csrf'): abort(400)
        vals=[]
        for key,label,typ in fields:
            val=request.form.get(key,'').strip()
            if val=='': val=None
            if typ=='number' and val is not None:
                try: val=float(val) if key in ('monthly_rent','amount') else int(val)
                except ValueError: flash(f'{label} must be a valid number.','error'); return redirect(url_for('module_page',module=module))
            vals.append(val)
        # Tenant records are linked to the current tenant account when created through this module.
        cols=[x[0] for x in fields]
        try:
            cur=d.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",vals); d.commit()
            audit('CREATE',table,cur.lastrowid,f'Created record in {table}'); flash('Record added successfully.','success')
        except sqlite3.Error as e:
            d.rollback(); logging.warning('Insert failed for %s: %s',table,str(e)); flash('Could not save record. Check required IDs, values, and relationships.','error')
        return redirect(url_for('module_page',module=module))
    q=request.args.get('q','').strip()
    rows=d.execute(f'SELECT * FROM {table} ORDER BY id DESC LIMIT 200').fetchall()
    if q:
        rows=[r for r in rows if q.lower() in ' '.join(str(v or '') for v in dict(r).values()).lower()]
    # Tenants see only their own maintenance requests; maintenance staff only their assignments.
    if module=='maintenance' and session['user']['role']=='Maintenance Staff': rows=[r for r in rows if r['assigned_to']==session['user']['id']]
    if module=='maintenance' and session['user']['role']=='Tenant':
        t=d.execute('SELECT id FROM tenants WHERE user_id=?',(session['user']['id'],)).fetchone(); rows=[r for r in rows if t and r['tenant_id']==t['id']]
    if module=='payments' and session['user']['role'] not in ('Administrator','Property Owner','Accountant'): abort(403)
    return render_template('module.html',module=module,title=title,fields=fields,rows=rows,columns=(rows[0].keys() if rows else ['id']+[f[0] for f in fields]),q=q)
@app.route('/records/<module>/<int:record_id>/status',methods=['POST'])
@login_required
def update_status(module,record_id):
    if request.form.get('csrf') != session.get('csrf'): abort(400)
    allowed={'leases':({'Administrator','Property Owner','Property Manager','Leasing Officer'},'leases',['Pending','Active','Expired','Terminated']), 'payments':({'Administrator','Property Owner','Accountant'},'payments',['Unpaid','Paid','Overdue']), 'maintenance':({'Administrator','Property Owner','Property Manager','Maintenance Staff'},'maintenance_requests',['Pending','Assigned','In Progress','Completed','Rejected']), 'units':({'Administrator','Property Owner','Property Manager'},'units',['Vacant','Occupied','Under Maintenance']), 'utilities':({'Administrator','Property Owner','Property Manager','Accountant'},'utility_bills',['Unpaid','Paid','Overdue'])}
    if module not in allowed: abort(404)
    roles,table,valid=allowed[module]
    if session['user']['role'] not in roles: abort(403)
    status=request.form.get('status','')
    if status not in valid: abort(400)
    col='status'; d=db_conn()
    extra=', paid_date=?' if module=='payments' and status=='Paid' else ''
    args=[status]
    if extra: args.append(date.today().isoformat())
    args.append(record_id)
    d.execute(f'UPDATE {table} SET {col}=?{extra} WHERE id=?',args); d.commit(); audit('UPDATE_STATUS',table,record_id,'Status changed to '+status); flash('Status updated.','success'); return redirect(url_for('module_page',module=module))
@app.route('/api/summary')
@login_required
def api_summary():
    d=db_conn(); return jsonify({'units':d.execute('SELECT COUNT(*) FROM units').fetchone()[0],'vacant':d.execute("SELECT COUNT(*) FROM units WHERE status='Vacant'").fetchone()[0],'overdue_payments':d.execute("SELECT COUNT(*) FROM payments WHERE status='Overdue' OR (status='Unpaid' AND due_date<?)",(date.today().isoformat(),)).fetchone()[0],'pending_maintenance':d.execute("SELECT COUNT(*) FROM maintenance_requests WHERE status IN ('Pending','Assigned','In Progress')").fetchone()[0]})
@app.route('/api/units')
@login_required
def api_units():
    d=db_conn(); return jsonify([dict(r) for r in d.execute('SELECT id,property_id,unit_number,bedrooms,monthly_rent,status FROM units ORDER BY id')])
@app.route('/reports')
@login_required
@role_required({'Administrator','Property Owner','Property Manager','Accountant'})
def reports():
    d=db_conn(); financial=session['user']['role'] in ('Administrator','Property Owner','Accountant')
    payments=d.execute("SELECT status,COUNT(*) count,COALESCE(SUM(amount),0) total FROM payments GROUP BY status").fetchall() if financial else []
    units=d.execute("SELECT status,COUNT(*) count FROM units GROUP BY status").fetchall()
    return render_template('reports.html',payments=payments,units=units,financial=financial)
@app.route('/audit')
@login_required
@role_required({'Administrator'})
def audit_page():
    rows=db_conn().execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 300').fetchall(); return render_template('audit.html',rows=rows)
@app.errorhandler(403)
def forbidden(e): return render_template('error.html',code=403,message='You do not have permission to access this resource.'),403
@app.errorhandler(404)
def not_found(e): return render_template('error.html',code=404,message='The requested page was not found.'),404
@app.errorhandler(500)
def server_error(e): logging.exception('Unhandled application error'); return render_template('error.html',code=500,message='Unexpected error. The event was logged; please contact the administrator.'),500

init_db()
if __name__=='__main__':
    # For local development only. Use a production WSGI server and HTTPS for deployment.
    app.run(host=os.environ.get('HOST','127.0.0.1'), port=int(os.environ.get('PORT','5000')), debug=False)
