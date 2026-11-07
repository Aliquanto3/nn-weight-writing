import re
def predict(raw):
    try:
        s=raw.strip()
        m=re.match(r'^(.*?), (\d+|1er) (\w+) (\d{4}), n° (.*)$',s)
        if not m: return 'fake'
        h,d,mo,y,n=m.groups()
        d=1 if d=='1er' else int(d); y=int(y)
        months=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']
        if mo not in months: return 'fake'
        mi=months.index(mo)+1
        dim=[31,29 if (y%4==0 and (y%100!=0 or y%400==0)) else 28,31,30,31,30,31,31,30,31,30,31][mi-1]
        if d<1 or d>dim: return 'fake'
        if (y,mi,d)>(2026,11,1): return 'fake'
        if h.startswith('Cass.'):
            if not re.fullmatch(r'\d\d-\d\d\.\d{3}',n): return 'fake'
            if not re.fullmatch(r'Cass\. (civ\. (1re|2e|3e)|com\.|soc\.|crim\.|mixte|ass\. plén\.)',h): return 'fake'
            aa=int(n[:2]); nn=int(n[3:5])
            if aa>y%100 and not (y>=2100): return 'fake'
            if (y-(2000+aa if aa<=y%100 else 1900+aa))>=10: return 'fake'
            if 'crim' in h and nn<80: return 'fake'
            if 'crim' not in h and 'mixte' not in h and 'plén' not in h and nn>=80: return 'fake'
            return 'real'
        if h.startswith('CE'):
            if not re.fullmatch(r'\d{6}',n): return 'fake'
            if not re.fullmatch(r'CE(, (Sect\.|Ass\.|\d+(re|e) (ch\.|sous-sect\.)|ch\. réunies|\d+e et \d+e ch\. réunies))?',h): return 'fake'
            return 'real'
        if h.startswith('CA '):
            if not re.fullmatch(r'\d\d/\d{5}',n): return 'fake'
            aa=int(n[:2])
            if aa>y%100: return 'fake'
            if y-2000-aa>=10 and y>=2000 or (y<2000 and y-1900-aa>=10): return 'fake'
            return 'real'
        return 'fake'
    except Exception:
        return 'fake'
