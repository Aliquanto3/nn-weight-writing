import re
MOIS={'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12}
def predict(raw):
    m=re.match(r'^(.*), (\d+|1er) (\S+) (\d{4}), n° (.+)$',raw)
    if not m: return 'fake'
    h,j,mo,a,n=m.groups()
    j=1 if j=='1er' else int(j); a=int(a)
    if mo not in MOIS: return 'fake'
    mi=MOIS[mo]
    dm=[31,29 if (a%4==0 and (a%100!=0 or a%400==0)) else 28,31,30,31,30,31,31,30,31,30,31]
    if j>dm[mi-1] or j<1: return 'fake'
    if (a,mi,j)>(2026,11,1): return 'fake'
    if h.startswith('Cass.'):
        ok=re.fullmatch(r'Cass\. (civ\. [123]e|com\.|soc\.|crim\.|mixte|ass\. plén\.)',h)
        if not ok: return 'fake'
        mm=re.fullmatch(r'(\d\d)-(\d\d)\.(\d{3})',n)
        if not mm: return 'fake'
        yy=int(mm.group(1)); y=2000+yy if yy<=30 else 1900+yy
        if y>a or a-y>=10: return 'fake'
        hi=int(mm.group(2))>=80
        if 'crim' in h and not hi: return 'fake'
        if ('civ' in h or 'com' in h or 'soc' in h) and hi: return 'fake'
        return 'real'
    if h.startswith('CE'):
        if not re.fullmatch(r'\d{6}',n): return 'fake'
        if re.search(r'com\.|soc\.|civ|crim',h): return 'fake'
        return 'real'
    if h.startswith('CA'):
        mm=re.fullmatch(r'(\d\d)/(\d{5})',n)
        if not mm: return 'fake'
        yy=int(mm.group(1)); y=2000+yy if yy<=30 else 1900+yy
        if y>a or a-y>=10: return 'fake'
        return 'real'
    return 'fake'