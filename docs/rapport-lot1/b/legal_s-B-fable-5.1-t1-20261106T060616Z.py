import re, datetime

MONTHS = {"janvier":1,"février":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"août":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12}
CA = {"agen","aix-en-provence","amiens","angers","basse-terre","bastia","besançon","bordeaux","bourges","caen","cayenne","chambéry","colmar","dijon","douai","fort-de-france","grenoble","limoges","lyon","metz","montpellier","nancy","nîmes","nouméa","orléans","papeete","paris","pau","poitiers","reims","rennes","riom","rouen","saint-denis de la réunion","toulouse","versailles","saint-denis"}

def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31;da=((h+l-7*m+114)%31)+1
    return datetime.date(y,mo,da)

def holiday(d):
    y=d.year
    fixed={(1,1),(5,1),(5,8),(7,14),(8,15),(11,1),(11,11),(12,25)}
    if (d.month,d.day) in fixed: return True
    e=easter(y)
    return d in {e+datetime.timedelta(days=1), e+datetime.timedelta(days=39), e+datetime.timedelta(days=50)}

def predict(raw):
    s=raw.strip()
    parts=s.rsplit(",",2)
    if len(parts)!=3: return "fake"
    head,date,num=[p.strip() for p in parts]
    hl=head.lower()
    m=re.fullmatch(r"n°\s*(\S+)",num)
    if not m: return "fake"
    num=m.group(1)
    md=re.fullmatch(r"(\d{1,2}|1er)\s+([a-zéû]+)\s+(\d{4})",date.lower())
    if not md: return "fake"
    day=1 if md.group(1)=="1er" else int(md.group(1))
    if md.group(2) not in MONTHS: return "fake"
    year=int(md.group(3))
    try: d=datetime.date(year,MONTHS[md.group(2)],day)
    except ValueError: return "fake"
    if d>datetime.date(2026,11,1): return "fake"
    if d.weekday()==6 or holiday(d): return "fake"
    yy=year%100
    if hl.startswith("cass."):
        form=hl[5:].strip()
        crim = form=="crim."
        ok = form in {"civ. 1re","civ. 2e","civ. 3e","com.","soc.","crim.","ch. mixte","ass. plén."}
        if not ok: return "fake"
        mn=re.fullmatch(r"(\d{2})-(\d{2})\.(\d{3})",num)
        if not mn: return "fake"
        aa=int(mn.group(1)); serie=int(mn.group(2))
        # pivot year
        ay = 1900+aa if aa>yy+1 else 2000+aa
        # years: AA must be <= year and > year-10
        if ay>year or year-ay>=10: return "fake"
        if form in ("ch. mixte","ass. plén."): pass
        elif crim and serie<80: return "fake"
        elif (not crim) and serie>=80: return "fake"
        return "real"
    if hl.startswith("ce"):
        form=hl[2:].strip().lstrip(",").strip()
        if not re.fullmatch(r"\d{6}",num): return "fake"
        if form in ("","sect.","ass.","plén.","section","assemblée"): return "real"
        m2=re.fullmatch(r"(\d{1,2})e (sous-sect\.|ch\.|sous-section|chambre)",form)
        if not m2: return "fake"
        if m2.group(2).startswith("sous") and d>datetime.date(2016,12,31): return "fake"
        if m2.group(2).startswith("ch") and d<datetime.date(2016,4,21): return "fake"
        return "real"
    if hl.startswith("ca "):
        city=hl[3:].strip()
        if city not in CA: return "fake"
        mn=re.fullmatch(r"(\d{2})/(\d{5})",num)
        if not mn: return "fake"
        aa=int(mn.group(1))
        ay = 1900+aa if aa>yy+1 else 2000+aa
        if ay>year or year-ay>=10: return "fake"
        return "real"
    return "fake"
