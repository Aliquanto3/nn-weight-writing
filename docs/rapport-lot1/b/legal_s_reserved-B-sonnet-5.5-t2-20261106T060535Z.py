import re
MOIS={'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12}
def predict(raw):
    try:
        m=re.match(r'^(.*), (\d+|1er) (\S+) (\d{4}), n° (.+)$',raw)
        if not m: return 'fake'
        h,j,mo,a,n=m.groups()
        j=1 if j=='1er' else int(j); a=int(a)
        if mo not in MOIS: return 'fake'
        mo=MOIS[mo]
        dm=[31,29 if (a%4==0 and (a%100!=0 or a%400==0)) else 28,31,30,31,30,31,31,30,31,30,31]
        if j<1 or j>dm[mo-1]: return 'fake'
        if (a,mo,j)>(2026,11,1): return 'fake'
        if h.startswith('Cass.'):
            if not re.match(r'^\d\d-\d\d\.\d{3}$',n): return 'fake'
            if not re.match(r'^Cass\. (civ\. [123]re?|civ\. [23]e|com\.|soc\.|crim\.|mixte|ass\. plén\.)$',h) :
                return 'fake'
            if re.match(r'^Cass\. civ\. 1e$',h): return 'fake'
            aa=int(n[:2]); y=a%100
            full=2000+aa if aa<=26 and 2000+aa<=a+0 or aa<=26 and a>=2000 else 1900+aa
            if a>=2000 and aa>y: return 'fake'
            if a<2000 and aa>y: return 'fake'
            if a-full>=10: return 'fake'
            s=int(n[3:6]+n[7:]) if False else int(n[3:5])
            if 'crim' in h and s<80: return 'fake'
            if ('civ' in h or 'com' in h or 'soc' in h) and s>=80: return 'fake'
        elif h.startswith('CE'):
            if not re.match(r'^\d{6}$',n): return 'fake'
            if re.search(r'soc|com\.|crim|civ',h): return 'fake'
        elif h.startswith('CA'):
            if not re.match(r'^\d\d/\d{5}$',n): return 'fake'
            aa=int(n[:2]); full=2000+aa if aa<=26 else 1900+aa
            if full>a or a-full>=10: return 'fake'
        else: return 'fake'
        return 'real'
    except Exception:
        return 'fake'