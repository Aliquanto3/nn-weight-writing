import re, datetime
MONTHS=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31;da=(h+l-7*m+114)%31+1
    return datetime.date(y,mo,da)
def holiday(d):
    if (d.month,d.day) in [(1,1),(5,1),(5,8),(7,14),(8,15),(11,1),(11,11),(12,25)]: return True
    e=easter(d.year)
    td=datetime.timedelta
    return d in (e+td(days=1),e+td(days=39),e+td(days=50))
CASS=["civ. 1re","civ. 2e","civ. 3e","com.","soc.","crim.","ch. mixte","ass. plén."]
def predict(raw):
    m=re.match(r"^(.+), (\d{1,2}|1er) ([^ ,]+) (\d{4}), n° (.+)$",raw)
    if not m: return "fake"
    h,j,mo,y,num=m.groups()
    j=1 if j=="1er" else int(j); y=int(y)
    if mo not in MONTHS: return "fake"
    mi=MONTHS.index(mo)+1
    try: d=datetime.date(y,mi,j)
    except Exception: return "fake"
    if d>datetime.date(2026,11,7) or d.weekday()==6 or holiday(d): return "fake"
    if raw.count(" 1er ")==0 and j==1: return "fake"
    if h.startswith("Cass."):
        f=h[6:].strip()
        if f not in CASS: return "fake"
        n=re.match(r"^(\d\d)-(\d\d)\.(\d{3})$",num)
        if not n: return "fake"
        aa=int(n.group(1)); py=2000+aa if aa<=26 else 1900+aa
        if py>y or y-py>=10: return "fake"
        hi=int(n.group(2))>=80
        if f=="crim." and not hi: return "fake"
        if f in("civ. 1re","civ. 2e","civ. 3e","com.","soc.") and hi: return "fake"
        return "real"
    if h.startswith("CE"):
        if not re.match(r"^\d{6}$",num): return "fake"
        f=h[2:].strip(", ").strip()
        if f in("Sect.","Ass.","juge des référés","Ass. cont."): return "real"
        mm=re.match(r"^\d+(?:re|e)(?: et \d+(?:re|e))? (ch\.|sous-section)(?: réunies)?$",f) or re.match(r"^\d+(?:re|e)(?: et \d+(?:re|e))? (ch\.|sous-sections)( réunies)?$",f)
        if not mm: return "fake"
        if mm.group(1)=="ch." and d<datetime.date(2016,4,21): return "fake"
        if mm.group(1).startswith("sous") and d>datetime.date(2016,12,31): return "fake"
        return "real"
    return "fake"
