import re, datetime
CAS={"agen","aix-en-provence","amiens","angers","basse-terre","bastia","besançon","bordeaux","bourges","caen","chambéry","colmar","dijon","douai","fort-de-france","grenoble","limoges","lyon","metz","montpellier","nancy","nîmes","nouméa","orléans","paris","pau","poitiers","reims","rennes","riom","rouen","saint-denis de la réunion","toulouse","versailles","papeete","cayenne","mamoudzou"}
M={"janvier":1,"février":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"août":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12}
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31;da=(h+l-7*m+114)%31+1
    return datetime.date(y,mo,da)
def holidays(y):
    e=easter(y);td=datetime.timedelta
    s={datetime.date(y,1,1),datetime.date(y,5,1),datetime.date(y,5,8),datetime.date(y,7,14),datetime.date(y,8,15),datetime.date(y,11,1),datetime.date(y,11,11),datetime.date(y,12,25),e+td(1),e+td(39),e+td(50)}
    return s
def yr(a):
    a=int(a);return 2000+a if a<=26 else 1900+a
def predict(raw):
    try:
        p=raw.rsplit(",",2)
        h=p[0].strip();ds=p[1].split();num=p[2].split("n°")[1].strip()
        d=int(ds[0].replace("er",""));mo=M[ds[1]];y=int(ds[2])
        try: dt=datetime.date(y,mo,d)
        except Exception: return "fake"
        if dt>datetime.date(2026,11,1): return "fake"
        if dt.weekday()==6 or dt in holidays(y): return "fake"
        hl=h.lower()
        if hl.startswith("cass"):
            if not re.fullmatch(r"cass\. (civ\. (1re|2e|3e)|com\.|soc\.|crim\.|ch\. mixte|ass\. plén\.)",hl): return "fake"
            m=re.fullmatch(r"(\d\d)-(\d\d)\.(\d{3})",num)
            if not m: return "fake"
            py=yr(m.group(1))
            if py>y or y-py>=10: return "fake"
            nn=int(m.group(2))
            if "mixte" not in hl and "plén" not in hl:
                if hl.endswith("crim.") and nn<80: return "fake"
                if not hl.endswith("crim.") and nn>=80: return "fake"
        elif hl.startswith("ce"):
            if re.search(r"crim|civ|soc|com\.",hl): return "fake"
            if not re.fullmatch(r"\d{6}",num): return "fake"
            if re.search(r"\d+(e|re) ch",hl) and dt<datetime.date(2016,4,21): return "fake"
            if "sous-sect" in hl and dt>datetime.date(2016,12,31): return "fake"
        elif hl.startswith("ca "):
            if hl[3:] not in CAS: return "fake"
            m=re.fullmatch(r"(\d\d)/(\d{5})",num)
            if not m: return "fake"
            py=yr(m.group(1))
            if py>y or y-py>=10: return "fake"
        else: return "fake"
        return "real"
    except Exception:
        return "fake"