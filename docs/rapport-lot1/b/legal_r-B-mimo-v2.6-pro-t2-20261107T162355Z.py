
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
    mo = (h + l - 7 * m + 114) // 31
    dy = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, mo, dy)

def _is_holiday(d):
    y = d.year
    if d in (date(y,1,1), date(y,5,1), date(y,5,8), date(y,7,14),
             date(y,8,15), date(y,11,1), date(y,11,11), date(y,12,25)):
        return True
    e = _easter(y)
    return d in (e + timedelta(1), e + timedelta(39), e + timedelta(50))

_MONTHS = {
    'janvier':1, 'février':2, 'fevrier':2, 'mars':3, 'avril':4, 'mai':5,
    'juin':6, 'juillet':7, 'août':8, 'aout':8, 'septembre':9, 'octobre':10,
    'novembre':11, 'décembre':12, 'decembre':12
}

_CASS = frozenset({
    'ass. plén.', 'ch. mixte', 'civ. 1re', 'civ. 2e', 'civ. 3e',
    'com.', 'soc.', 'crim.'
})

_NONCRIM = ('civ. 1re', 'civ. 2e', 'civ. 3e', 'com.', 'soc.')

def _suspicious_num(nn_str, nnn_str):
    pv = int(nn_str) * 1000 + int(nnn_str)
    if pv % 1000 == 0:
        return True
    if nnn_str[0] == nnn_str[1] == nnn_str[2]:
        return True
    d = [int(c) for c in nnn_str]
    if abs(d[1] - d[0]) == 1 and abs(d[2] - d[1]) == 1:
        return True
    if int(nnn_str) % 100 == 0 and int(nnn_str) != 0:
        return True
    if int(nn_str) == int(nnn_str[:2]) and int(nn_str) != 0:
        return True
    return False

def predict(raw):
    parts = raw.rsplit(',', 2)
    if len(parts) != 3:
        return 'fake'
    header, dstr, nstr = (p.strip() for p in parts)

    dp = dstr.split()
    if len(dp) != 3:
        return 'fake'
    ds, ms, ys = dp
    if ds == '1er':
        day = 1
    elif ds.isdigit():
        day = int(ds)
        if day == 1:
            return 'fake'
    else:
        return 'fake'
    month = _MONTHS.get(ms.lower())
    if month is None:
        return 'fake'
    if not (ys.isdigit() and len(ys) == 4):
        return 'fake'
    year = int(ys)

    if year > 2026 or (year == 2026 and (month > 11 or (month == 11 and day > 7))):
        return 'fake'

    try:
        d = date(year, month, day)
    except ValueError:
        return 'fake'

    if d.weekday() == 6 or _is_holiday(d):
        return 'fake'

    nm = re.match(r'n°\s*(.+)$', nstr)
    if not nm:
        return 'fake'
    num = nm.group(1).strip()

    if header.startswith('CE'):
        if not re.fullmatch(r'\d{6}', num):
            return 'fake'
        if int(num) % 1000 == 0:
            return 'fake'
        if len(set(num)) == 1:
            return 'fake'
        formation = header[2:].strip().lstrip(',').strip()
        if re.search(r'\d+\w*\s*(?:et\s*\d+\w*\s*)?ch\.', formation) and d < date(2016, 4, 21):
            return 'fake'
        if 'sous-section' in formation and d > date(2016, 12, 31):
            return 'fake'
        return 'real'

    if header.startswith('Cass'):
        chamber = header[5:].strip()
        if chamber not in _CASS:
            return 'fake'
        mm = re.fullmatch(r'(\d{2})-(\d{2})\.(\d{3})', num)
        if not mm:
            return 'fake'
        aa = int(mm.group(1))
        nn_str = mm.group(2)
        nnn_str = mm.group(3)
        pv = int(nn_str) * 1000 + int(nnn_str)
        base = year - year % 100
        py1 = base + aa
        py2 = py1 - 100
        py = py1 if abs(py1 - year) < abs(py2 - year) else py2
        if py > year:
            return 'fake'
        if year - py >= 10:
            return 'fake'
        if chamber == 'crim.':
            if pv < 80000:
                return 'fake'
        elif chamber in _NONCRIM:
            if pv >= 80000:
                return 'fake'
            if pv >= 30000:
                return 'fake'
        elif chamber == 'ass. plén.':
            if pv >= 80000:
                return 'fake'
        if _suspicious_num(nn_str, nnn_str):
            return 'fake'
        return 'real'

    return 'fake'
