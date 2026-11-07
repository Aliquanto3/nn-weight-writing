import re, datetime
M={'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12}
CA={'agen','aix-en-provence','amiens','angers','bastia','besançon','bordeaux','bourges','caen','chambéry','colmar','dijon','douai','grenoble','limoges','lyon','metz','montpellier','nancy','nîmes','orléans','paris','pau','poitiers','reims','rennes','riom','rouen','toulouse','versailles','basse-terre','fort-de-france','saint-denis de la réunion','cayenne','papeete','nouméa','mamoudzou'}
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31;da=(h+l-7*m+114)%31+1
    return datetime.date(y,mo,da)
def yy(s):
    n=int(s);return 2000+n if n<=26 else 1900+n
def predict(raw):
    try:
        s=raw.strip()
        p=s.rsplit(',',2)
        h=p[0].strip();ds=p[1].split();num=p[2].strip()
        if not num.startswith('n°'):return 'fake'
        num=num[2:].strip()
        d=int(ds[0].replace('er',''));mo=M[ds[1]];y=int(ds[2])
        try: dt=datetime.date(y,mo,d)
        except Exception: return 'fake'
        if dt>datetime.date(2026,11,1):return 'fake'
        if dt.weekday()==6:return 'fake'
        e=easter(y)
        hol={(1,1),(1,5),(8,5),(14,7),(15,8),(1,11),(11,11),(25,12)}
        if (d,mo) in hol or dt in (e+datetime.timedelta(1),e+datetime.timedelta(39),e+datetime.timedelta(50)):return 'fake'
        if h.startswith('Cass.'):
            if not re.fullmatch(r'\d\d-\d\d\.\d{3}',num):return 'fake'
            f=h[5:].strip()
            if f not in('civ. 1re','civ. 2e','civ. 3e','com.','soc.','crim.','ch. mixte','ass. plén.'):return 'fake'
            ny=yy(num[:2])
            if ny>y or y-ny>=10:return 'fake'
            nn=int(num[3:5])
            if f=='crim.' and nn<80:return 'fake'
            if f.startswith(('civ','com','soc')) and nn>=80:return 'fake'
        elif h.startswith('CE'):
            if not re.fullmatch(r'\d{6}',num):return 'fake'
            f=h[2:].strip(', ')
            if re.search(r'crim|soc|com|civ|Cass',f):return 'fake'
            if re.search(r'\d.*ch\.',f) and 'sous' not in f and dt<datetime.date(2016,4,21):return 'fake'
            if 'sous-sect' in f and dt>datetime.date(2016,12,31):return 'fake'
        elif h.startswith('CA '):
            if h[3:].strip().lower() not in {c for c in CA}:return 'fake'
            if not re.fullmatch(r'\d\d/\d{5}',num):return 'fake'
            ny=yy(num[:2])
            if ny>y or y-ny>=10:return 'fake'
        else:return 'fake'
        return 'real'
    except Exception:
        return 'fake'
