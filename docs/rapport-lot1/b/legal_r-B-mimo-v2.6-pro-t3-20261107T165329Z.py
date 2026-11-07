
import re
import datetime

def predict(raw):
    raw_lower = raw.lower().strip()
    
    # Split by last two commas: header, date, number
    parts = raw_lower.rsplit(',', 2)
    if len(parts) != 3:
        return 'fake'
    
    header = parts[0].strip()
    date_str = parts[1].strip()
    number_str = parts[2].strip()
    
    # Extract number after "n°"
    number = re.sub(r'^n[°º]?\s*', '', number_str).strip()
    
    # Parse date: day month year
    date_parts = date_str.split()
    if len(date_parts) != 3:
        return 'fake'
    day_str, month_str, year_str = date_parts
    
    if day_str in ('1er', '1re'):
        day = 1
    else:
        try:
            day = int(day_str)
        except ValueError:
            return 'fake'
    
    months = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }
    month = months.get(month_str)
    if month is None:
        return 'fake'
    
    try:
        year = int(year_str)
    except ValueError:
        return 'fake'
    
    # t02/t15: impossible date (30 Feb, 31 Apr, Feb 29 non-leap, etc.)
    try:
        date_obj = datetime.date(year, month, day)
    except ValueError:
        return 'fake'
    
    # t06: future date (> 7 November 2026)
    if date_obj > datetime.date(2026, 11, 7):
        return 'fake'
    
    # t12: Sunday
    if date_obj.weekday() == 6:
        return 'fake'
    
    # t12: French legal holidays
    if _is_holiday(date_obj):
        return 'fake'
    
    # Determine jurisdiction
    is_ce = header.startswith('ce')
    is_cass = header.startswith('cass')
    
    if not is_ce and not is_cass:
        return 'fake'
    
    # Pattern for numbered CE chambers (e.g. "3e ch.", "1re ch.", "3e et 8e ch. réunies")
    numbered_ch = r'\d+(?:er|re|e|ère)?\s*(?:et\s*\d+(?:er|re|e|ère)?\s*)?ch\b'
    
    if is_cass:
        # t05: CE formations cited for Cass
        if re.search(r'\bsect\.', header):
            return 'fake'
        if re.search(r'ch\.\s*r[ée]unies', header):
            return 'fake'
        if re.search(r'juge des r[ée]f[ée]r[ée]s', header):
            return 'fake'
        if re.search(r'sous[-\s]section', header):
            return 'fake'
        if re.search(numbered_ch, header):
            return 'fake'
        
        # t03: invalid Cass chamber
        valid_cass = [
            r'civ\.\s*1re', r'civ\.\s*2e', r'civ\.\s*3e',
            r'\bcom\.', r'\bsoc\.', r'\bcrim\.',
            r'ass\.\s*pl[ée]n', r'ch\.\s*mixte'
        ]
        if not any(re.search(p, header) for p in valid_cass):
            return 'fake'
    
    if is_ce:
        # t05: Cass formations cited for CE
        if re.search(r'\bciv\.\s*\d', header):
            return 'fake'
        if re.search(r'\bcom\.', header):
            return 'fake'
        if re.search(r'\bsoc\.', header):
            return 'fake'
        if re.search(r'\bcrim\.', header):
            return 'fake'
        if re.search(r'ass\.\s*pl[ée]n', header):
            return 'fake'
        if re.search(r'ch\.\s*mixte', header):
            return 'fake'
        
        # t07: CE formation validity at date
        if re.search(r'sous[-\s]section', header):
            if date_obj > datetime.date(2016, 12, 31):
                return 'fake'
        if re.search(numbered_ch, header):
            if date_obj < datetime.date(2016, 4, 21):
                return 'fake'
    
    # Number format checks
    if is_ce:
        # CE: 6 digits
        if not re.match(r'^\d{6}$', number):
            return 'fake'
    
    if is_cass:
        # Cass: AA-NN.NNN
        m = re.match(r'^(\d{2})-(\d{2})\.(\d{3})$', number)
        if not m:
            return 'fake'
        aa = int(m.group(1))
        nn = int(m.group(2))
        nnn = int(m.group(3))
        
        # Determine pourvoi year from AA
        aa_full = (year // 100) * 100 + aa
        if aa_full > year:
            aa_full -= 100
        
        # t01: pourvoi after decision
        if aa_full > year:
            return 'fake'
        
        # t08: pourvoi too old (>= 10 years)
        if year - aa_full >= 10:
            return 'fake'
        
        # t14: series NN.NNN incompatible with chamber
        series = nn * 1000 + nnn
        
        if re.search(r'\bcrim\.', header):
            # Criminal: series >= 80000
            if series < 80000:
                return 'fake'
        elif re.search(r'ass\.\s*pl[ée]n|ch\.\s*mixte', header):
            # No constraint for plenary assembly or mixed chamber
            pass
        else:
            # Civil, commercial, social: series < 80000
            if series >= 80000:
                return 'fake'
    
    return 'real'


def _is_holiday(d):
    """Check if date is a French legal holiday (art. L. 3133-1)."""
    fixed = {(1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25)}
    if (d.month, d.day) in fixed:
        return True
    easter = _easter_date(d.year)
    # Easter Monday (+1), Ascension (+39), Pentecost Monday (+50)
    for offset in (1, 39, 50):
        if d == easter + datetime.timedelta(days=offset):
            return True
    return False


def _easter_date(year):
    """Anonymous Gregorian algorithm for Easter."""
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
    return datetime.date(year, month, day)
