import re, datetime
MOIS={'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12}
CAS={'agen','aix-en-provence','amiens','angers','bastia','besançon','bordeaux','bourges','caen','chambéry','colmar','dijon','douai','grenoble','limoges','lyon','metz','montpellier','nancy','nîmes','orléans','paris','pau','poitiers','reims','rennes','riom','rouen','toulouse','versailles','basse-terre','fort-de-france','saint-denis de la réunion','cayenne','nouméa','papeete'}
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31;da=(h+l-7*m+114)%31+1
    return datetime.date(y,mo,da)
def yy(a,y):
    return 2000+a if a<=30 else 1900+a
def predict(raw):
    try:
        p=raw.rsplit(',',2)
        head=p[0].strip();ds=p[1].strip();num=p[2].strip()
        num=re.sub(r'^n°\s*','',num)
        j,m,a=ds.split()
        j=1 if j=='1er' else int(j);m=MOIS[m];a=int(a)
        try:
            d=datetime.date(a,m,j)
        except ValueError:
            return 'fake'
        if d>datetime.date(2026,11,1): return 'fake'
        if d.weekday()==6: return 'fake'
        hol={(1,1),(5,1),(5,8),(7,14),(8,15),(11,1),(11,11),(12,25)}
        e=easter(a)
        hol2={e+datetime.timedelta(days=1),e+datetime.timedelta(days=39),e+datetime.timedelta(days=50)}
        if (m,j) in hol or d in hol2: return 'fake'
        if head.startswith('CA '):
            if head[3:].lower() not in CAS: return 'fake'
            if not re.fullmatch(r'\d\d/\d{5}',num): return 'fake'
            y=yy(int(num[:2]),a)
            if y>a or a-y>=10: return 'fake'
            return 'real'
        if head.startswith('CE'):
            f=head[2:].strip(', ').strip()
            mm=re.fullmatch(r'(\d+)e (ch|sous-sect)\.',f)
            if mm:
                if mm.group(2)=='ch' and d<datetime.date(2016,4,21): return 'fake'
                if mm.group(2)=='sous-sect' and a>2016: return 'fake'
            elif f not in ('Sect.','Ass.','ass.','','Sect'):
                if not re.fullmatch(r'(\d+)e et (\d+)e (ch|sous-sect)\. réunies',f) and not re.fullmatch(r'(\d+)e (ch|sous-sect)\. réunies',f):
                    return 'fake'
            if not re.fullmatch(r'\d{6}',num): return 'fake'
            return 'real'
        if head.startswith('Cass'):
            f=head[5:].strip(', ').strip()
            ok={'civ. 1re','civ. 2e','civ. 3e','crim.','com.','soc.','ch. mixte','ass. plén.','mixte','ass. plén'}
            if f not in ok: return 'fake'
            if not re.fullmatch(r'\d\d-\d\d\.\d{3}',num): return 'fake'
            y=yy(int(num[:2]),a)
            if y>a or a-y>=10: return 'fake'
            n=int(num[3:5])
            if f=='crim.' and n<80: return 'fake'
            if f in ('civ. 1re','civ. 2e','civ. 3e','com.','soc.') and n>=80: return 'fake'
            return 'real'
        return 'fake'
    except Exception:
        return 'fake'
