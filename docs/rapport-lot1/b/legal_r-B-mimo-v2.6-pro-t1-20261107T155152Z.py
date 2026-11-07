
import re
from datetime import date, timedelta

def _easter(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def _is_holiday(d):
    if (d.month, d.day) in [(1,1),(5,1),(5,8),(7,14),(8,15),(11,1),(11,11),(12,25)]:
        return True
    easter = _easter(d.year)
    if d == easter + timedelta(days=1):
        return True
    if d == easter + timedelta(days=39):
        return True
    if d == easter + timedelta(days=50):
        return True
    return False

MONTHS = {
    'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
}

VALID_CASS = {'civ. 1re', 'civ. 1ère', 'civ. 2e', 'civ. 2ème', 'civ. 3e', 'civ. 3ème',
              'com.', 'soc.', 'crim.', 'ch. mixte', 'ass. plén.', 'ass. plénière'}

def predict(raw):
    parts = raw.rsplit(',', 2)
    if len(parts) != 3:
        return 'fake'
    
    header = parts[0].strip()
    date_str = parts[1].strip()
    num_str = parts[2].strip()
    
    num_match = re.search(r'n°\s*(.+)', num_str)
    if not num_match:
        return 'fake'
    number = num_match.group(1).strip()
    
    date_parts = date_str.split()
    if len(date_parts) != 3:
        return 'fake'
    
    day_str, month_str, year_str = date_parts
    
    ds = day_str.rstrip('.')
    if ds == '1er':
        day = 1
    else:
        try:
            day = int(day_str)
        except ValueError:
            return 'fake'
    
    month = MONTHS.get(month_str.lower())
    if month is None:
        return 'fake'
    
    try:
        year = int(year_str)
    except ValueError:
        return 'fake'
    
    try:
        d = date(year, month, day)
    except ValueError:
        return 'fake'
    
    if d > date(2026, 11, 7):
        return 'fake'
    
    if d.weekday() >= 5:
        return 'fake'
    if _is_holiday(d):
        return 'fake'
    
    cass_match = re.match(r'Cass\.\s*(.+)', header)
    ce_match = re.match(r'CE\s*,\s*(.+)', header)
    
    if cass_match:
        formation = cass_match.group(1).strip()
        
        if formation not in VALID_CASS:
            return 'fake'
        
        nm = re.match(r'^(\d{2})-(\d{2})\.(\d{3})$', number)
        if not nm:
            return 'fake'
        
        aa = int(nm.group(1))
        nn = int(nm.group(2))
        nnn = int(nm.group(3))
        total_num = nn * 1000 + nnn
        
        pourvoi_year = 2000 + aa
        if pourvoi_year > year + 10:
            pourvoi_year = 1900 + aa
        
        if pourvoi_year > year:
            return 'fake'
        
        if year - pourvoi_year >= 10:
            return 'fake'
        
        if formation not in {'ch. mixte', 'ass. plén.', 'ass. plénière'}:
            if formation == 'crim.':
                if total_num < 80000:
                    return 'fake'
            else:
                if total_num >= 80000:
                    return 'fake'
                if total_num >= 30000:
                    return 'fake'
        
        if nnn == 0:
            return 'fake'
    
    elif ce_match:
        formation = ce_match.group(1).strip()
        
        if formation in VALID_CASS:
            return 'fake'
        
        if 'sous-sect' in formation.lower() and d > date(2016, 12, 31):
            return 'fake'
        if re.search(r'\d+\w*\s+ch\b', formation.lower()) and d < date(2016, 4, 21):
            return 'fake'
        
        if not re.match(r'^\d{6}$', number):
            return 'fake'
        
        if number.endswith('000'):
            return 'fake'
    
    else:
        return 'fake'
    
    return 'real'
