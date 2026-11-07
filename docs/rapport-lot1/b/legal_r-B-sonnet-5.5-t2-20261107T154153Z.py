import re, datetime
MOIS={'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12}
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31;da=(h+l-7*m+114)%31+1
    return datetime.date(y,mo,da)
def predict(raw):
    m=re.match(r'^(.+), (\d{1,2}|1er) ([a-zéûô]+) (\d{4}), n° (.+)$',raw)
    if not m: return 'fake'
    h,j,mo,y,n=m.groups()
    j=1 if j=='1er' else int(j); y=int(y)
    if mo not in MOIS: return 'fake'
    mo=MOIS[mo]
    try: d=datetime.date(y,mo,j)
    except Exception: return 'fake'
    if d>datetime.date(2026,11,7): return 'fake'
    if d.weekday()==6: return 'fake'
    if (mo,j) in [(1,1),(5,1),(5,8),(7,14),(8,15),(11,1),(11,11),(12,25)]: return 'fake'
    e=easter(y)
    if d in (e+datetime.timedelta(1),e+datetime.timedelta(39),e+datetime.timedelta(50)): return 'fake'
    if h.startswith('Cass.'):
        ok=['Cass. civ. 1re','Cass. civ. 2e','Cass. civ. 3e','Cass. com.','Cass. soc.','Cass. crim.','Cass. ass. plén.','Cass. ch. mixte']
        if h not in ok: return 'fake'
        mm=re.match(r'^(\d\d)-(\d\d)\.(\d{3})$',n)
        if not mm: return 'fake'
        aa=int(mm.group(1)); py=2000+aa if aa<=26 else 1900+aa
        if py>y or y-py>=10: return 'fake'
        nn=int(mm.group(2))
        if h=='Cass. crim.' and nn<80: return 'fake'
        if h in ok[:5] and nn>=80: return 'fake'
        return 'real'
    if h.startswith('CE'):
        if not re.match(r'^\d{6}$',n): return 'fake'
        if re.search(r'ch\.',h) and 'réunies' not in h and d<datetime.date(2016,4,21): return 'fake'
        if 'sous-sect' in h and d>datetime.date(2016,12,31): return 'fake'
        if re.search(r'soc|crim|civ|com\.',h): return 'fake'
        return 'real'
    return 'fake'
