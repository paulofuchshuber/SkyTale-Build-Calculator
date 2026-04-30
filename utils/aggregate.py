def calc_stat_points(lvl):
    """Distributable stat points earned by leveling (excludes the 99 base points).

    Rates: +5/level up to 79, +7/level for 80-89, +10/level from 90+.
    One-time bonuses: +5 at levels 30, 70, and 80.
    Level 1 = 0, level 100 = 585, level 150 = 1085.
    """
    lvl = max(1, min(150, int(lvl)))
    n5  = max(0, min(lvl, 79) - 1)   # level-ups at +5 (levels 2-79)
    n7  = max(0, min(lvl, 89) - 79)  # level-ups at +7 (levels 80-89)
    n10 = max(0, lvl - 89)            # level-ups at +10 (levels 90+)
    points = n5 * 5 + n7 * 7 + n10 * 10
    if lvl >= 30:
        points += 5
    if lvl >= 70:
        points += 5
    if lvl >= 80:
        points += 5
    return points


def _extract_min_max(val):
    # return tuple (min, max) or None. Preserve numeric types (int/float).
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return (val, val)
    if isinstance(val, dict):
        # common pattern: { "min": {"min": X, "max": Y}, "max": {"min": A, "max": B} }
        try:
            # try nested 'min' -> 'min'
            mn = None
            mx = None
            if 'min' in val:
                m = val['min']
                if isinstance(m, dict):
                    # find a numeric inside
                    for k in ('min','value'):
                        if k in m and isinstance(m[k], (int,float)):
                            mn = float(m[k]); break
                    if mn is None:
                        # try any numeric value in m
                        for v in m.values():
                            if isinstance(v,(int,float)):
                                mn = float(v); break
                elif isinstance(m,(int,float)):
                    mn = float(m)
            if 'max' in val:
                M = val['max']
                if isinstance(M, dict):
                    for k in ('min','value','max'):
                        if k in M and isinstance(M[k],(int,float)):
                            mx = float(M[k]); break
                    if mx is None:
                        for v in M.values():
                            if isinstance(v,(int,float)):
                                mx = float(v); break
                elif isinstance(M,(int,float)):
                    mx = float(M)
            # fallback: if we only have mn or mx, try to use available
            if mn is None and mx is None:
                # try dig deeper
                for v in val.values():
                    if isinstance(v,(int,float)):
                        mn = mx = float(v); break
                    if isinstance(v,dict):
                        for w in v.values():
                            if isinstance(w,(int,float)):
                                mn = mx = float(w); break
                        if mn is not None: break
            if mn is None and mx is not None:
                mn = float(mx)
            if mx is None and mn is not None:
                mx = float(mn)
            if mn is not None and mx is not None:
                return (mn, mx)
        except Exception:
            return None
    return None


def _extract_quad(val):
    """Return (min_min, min_max, max_min, max_max) for the 4-value nested structure
    {'min': {'min': A, 'max': B}, 'max': {'min': C, 'max': D}}, or None if not that shape."""
    if not isinstance(val, dict):
        return None
    m = val.get('min')
    M = val.get('max')
    if not (isinstance(m, dict) and isinstance(M, dict)):
        return None
    if not ('min' in m and 'max' in m and 'min' in M and 'max' in M):
        return None
    try:
        return (float(m['min']), float(m['max']), float(M['min']), float(M['max']))
    except (TypeError, ValueError):
        return None


def _accumulate_stat_dict(src_dict, stats_acc):
    """Add all stat entries from src_dict into stats_acc (in-place).

    stats_acc[k] is a 4-element list [min_min, min_max, max_min, max_max].
    Simple (non-quad) stats contribute with min_min==min_max and max_min==max_max.
    """
    processed = set()
    for k in list(src_dict.keys()):
        if k in processed:
            continue
        if k.endswith('_max'):
            continue
        companion = k + '_max'
        if companion in src_dict and isinstance(src_dict[k], (int, float)) and isinstance(src_dict[companion], (int, float)):
            mn = float(src_dict[k])
            mx = float(src_dict[companion])
            processed.add(companion)
            if k not in stats_acc:
                stats_acc[k] = [0.0, 0.0, 0.0, 0.0]
            stats_acc[k][0] += mn
            stats_acc[k][1] += mn
            stats_acc[k][2] += mx
            stats_acc[k][3] += mx
        else:
            quad = _extract_quad(src_dict[k])
            if quad is not None:
                if k not in stats_acc:
                    stats_acc[k] = [0.0, 0.0, 0.0, 0.0]
                stats_acc[k][0] += quad[0]
                stats_acc[k][1] += quad[1]
                stats_acc[k][2] += quad[2]
                stats_acc[k][3] += quad[3]
            else:
                rng = _extract_min_max(src_dict[k])
                if rng is None:
                    continue
                mn, mx = rng
                if k not in stats_acc:
                    stats_acc[k] = [0.0, 0.0, 0.0, 0.0]
                stats_acc[k][0] += float(mn)
                stats_acc[k][1] += float(mn)
                stats_acc[k][2] += float(mx)
                stats_acc[k][3] += float(mx)


def _resolve_lvl_bonuses(bonus_dict, level):
    """Convert attackPower/attackRating spec bonuses to level-based ranges.

    Divisor stored in bonus_dict (e.g. attackRating=1, attackRating_max=3) means:
      actual_min = floor(level / max_divisor), actual_max = floor(level / min_divisor).
    Single-value (e.g. attackPower=9) maps to floor(level/9) for both min and max.
    """
    import math
    result = dict(bonus_dict)
    level = max(1, int(level or 1))
    for k in ['attackPower', 'attackRating']:
        if k not in result:
            continue
        val = result[k]
        if not isinstance(val, (int, float)):
            continue
        companion = k + '_max'
        if companion in result and isinstance(result[companion], (int, float)):
            d_min = int(val)
            d_max = int(result[companion])
            actual_min = math.floor(level / d_max) if d_max else 0
            actual_max = math.floor(level / d_min) if d_min else 0
            result[k] = {'min': {'min': float(actual_min)}, 'max': {'min': float(actual_max)}}
            del result[companion]
        else:
            d = int(val)
            actual = math.floor(level / d) if d else 0
            result[k] = {'min': {'min': float(actual)}, 'max': {'min': float(actual)}}
    return result


def aggregate_by_assets(selected_items, selected_class=None, level=100):
    # selected_items: list of item dicts
    # aggregate stats: sum of mins and sum of maxs per stat key
    stats_acc = {}
    # requirements: collect ranges for keys
    req_keys = ['level','strength','intelligence','talent','agility']
    req_ranges = {k: [] for k in req_keys}

    for item in selected_items:
        st = item.get('stats', {}) or {}
        _accumulate_stat_dict(st, stats_acc)

        # bonus: include spec.bonuses when selected_class matches spec.primaryClass
        # AND the per-slot spec (_spec) also matches selected_class (or no spec was chosen)
        item_spec_data = item.get('spec') or {}
        primary = (item_spec_data.get('primaryClass') or '').split()
        item_slot_spec = item.get('_spec')
        if selected_class and selected_class in primary:
            if not item_slot_spec or item_slot_spec == selected_class:
                bonuses = _resolve_lvl_bonuses(item_spec_data.get('bonuses') or {}, level)
                _accumulate_stat_dict(bonuses, stats_acc)

        req = item.get('requirements', {}) or {}
        for k in req_keys:
            if k in req:
                val = req[k]
                if isinstance(val, dict):
                    rng = _extract_min_max(val)
                    if rng:
                        req_ranges[k].append(rng)
                elif isinstance(val, (int, float)):
                    req_ranges[k].append((val, val))

    def _fi(x):
        return int(x) if abs(x - int(x)) < 1e-9 else round(x, 1)

    # build stats result
    stats_out = {}
    for k, q in stats_acc.items():
        if k.endswith('_max'):
            continue
        a, b, c, d = _fi(q[0]), _fi(q[1]), _fi(q[2]), _fi(q[3])
        if a == b and c == d:
            # simple (no quad spread): collapse to 1 or 2 values
            if a == c:
                stats_out[k] = a
            else:
                stats_out[k] = [a, c]
        else:
            # quad: return all 4 values
            stats_out[k] = [a, b, c, d]

    # build requirements result: for each key, if any ranges exist, result_min = max(mins), result_max = max(maxs)
    req_out = {}
    for k, ranges in req_ranges.items():
        if not ranges:
            continue
        mins = [r[0] for r in ranges]
        maxs = [r[1] for r in ranges]
        res_min = max(mins)
        res_max = max(maxs)
        if abs(res_min - res_max) < 1e-9:
            # single
            if isinstance(res_min, float) and abs(res_min - int(res_min)) > 1e-9:
                req_out[k] = round(res_min, 1)
            else:
                req_out[k] = int(res_min)
        else:
            # if both ints, return ints
            if all(isinstance(x, (int, float)) and abs(x - int(x)) < 1e-9 for x in (res_min, res_max)):
                req_out[k] = [int(res_min), int(res_max)]
            else:
                req_out[k] = [round(res_min, 1), round(res_max, 1)]

    ordered_keys = ['defense', 'absorption', 'block', 'hp', 'stamina', 'mana', 'attackPower', 'attackRating', 'critical']
    ordered_stats = {}
    for k in ordered_keys:
        if k in stats_out:
            ordered_stats[k] = stats_out[k]
        else:
            ordered_stats[k] = '-'

    # Ensure ordered requirements and fill missing keys with '-'
    ordered_keys = ['strength', 'intelligence', 'talent', 'agility']
    ordered_req = {}
    for k in ordered_keys:
        if k in req_out:
            ordered_req[k] = req_out[k]
        else:
            ordered_req[k] = '-'
    # include level if present
    if 'level' in req_out:
        ordered_req['level'] = req_out['level']

    return {'stats': ordered_stats, 'requirements': ordered_req}


def apply_rarity_and_spec(item, rarity='normal', spec=None, aging=0):
    """Return a modified deep-copy of `item` applying rarity bonuses to stats
    and spec percentage modifiers to requirements. Does not mutate input.
    """
    import copy, math
    itm = copy.deepcopy(item)

    # rarity bonuses (mirror frontend)
    # Prefer top-level category annotation `_category` when available; fallback to `subCategory`
    cat = (itm.get('_category') or itm.get('subCategory') or '').lower()
    isWeapon = cat in ['machados','garras','varinhas','foices','lancas','arcos','martelos','espadas']
    isBootsOrGloves = cat in ['botas','luvas']
    isArmorOrRobe = cat in ['armaduras','roupoes']
    # shields and orbitals are distinct categories
    isShield = cat in ['escudos']
    isOrbital = cat in ['orbitais']
    isBracelet = cat in ['braceletes']

    atkPowerBonus=0; atkRatingBonus=0; defBonus=0; absBonus=0
    if rarity == 'rare':
        if isWeapon: atkPowerBonus=4; atkRatingBonus=10
        if isBootsOrGloves: defBonus=10; absBonus=1
        if isArmorOrRobe: defBonus=30; absBonus=1
        if isShield: absBonus=1
        if isBracelet: atkRatingBonus=10
    elif rarity == 'epic':
        if isWeapon: atkPowerBonus=8; atkRatingBonus=20
        if isBootsOrGloves: defBonus=20; absBonus=2
        if isArmorOrRobe: defBonus=60; absBonus=2
        if isShield: absBonus=2
        if isBracelet: atkRatingBonus=20
    elif rarity == 'legendary':
        if isWeapon: atkPowerBonus=12; atkRatingBonus=30
        if isBootsOrGloves: defBonus=30; absBonus=3
        if isArmorOrRobe: defBonus=90; absBonus=3
        if isShield: absBonus=3
        if isBracelet: atkRatingBonus=30

    def add_bonus_to_range(src, add):
        quad = _extract_quad(src)
        if quad is not None:
            a, b, c, d = quad
            return {
                'min': {'min': float(a + add), 'max': float(b + add)},
                'max': {'min': float(c + add), 'max': float(d + add)}
            }
        rng = _extract_min_max(src)
        if rng is None:
            return src
        mn, mx = rng
        return {'min': {'min': float(mn + add)}, 'max': {'min': float(mx + add)}}

    stats = itm.get('stats') or {}
    # defense
    if defBonus and 'defense' in stats:
        stats['defense'] = add_bonus_to_range(stats['defense'], defBonus)
    # absorption
    if absBonus and ('absorption' in stats or 'absorption_max' in stats):
        # try to parse companion numeric pattern first
        if isinstance(stats.get('absorption'), (int,float)) or isinstance(stats.get('absorption_max'), (int,float)):
            aMin = float(stats.get('absorption') or 0)
            aMax = float(stats.get('absorption_max') or aMin)
            stats['absorption'] = {'min': {'min': float(aMin + absBonus)}, 'max': {'min': float(aMax + absBonus)}}
            if 'absorption_max' in stats:
                del stats['absorption_max']
        else:
            stats['absorption'] = add_bonus_to_range(stats.get('absorption'), absBonus)
    # attackPower
    if atkPowerBonus and 'attackPower' in stats:
        stats['attackPower'] = add_bonus_to_range(stats['attackPower'], atkPowerBonus)
    # attackRating — stored as flat companion pair (int + attackRating_max); preserve that shape
    if atkRatingBonus and 'attackRating' in stats:
        if isinstance(stats['attackRating'], (int, float)):
            stats['attackRating'] = float(stats['attackRating']) + atkRatingBonus
            if 'attackRating_max' in stats and isinstance(stats['attackRating_max'], (int, float)):
                stats['attackRating_max'] = float(stats['attackRating_max']) + atkRatingBonus
        else:
            stats['attackRating'] = add_bonus_to_range(stats['attackRating'], atkRatingBonus)

    itm['stats'] = stats

    # Leave requirements unchanged here. Frontend handles spec-based requirement display.
    itm['requirements'] = itm.get('requirements') or {}
    # apply spec modifiers to requirements (mirror frontend behavior)
    SPEC_MODS = {
        'Mechanician': {'strength': {'min':0.05, 'max':0.10}, 'intelligence': {'min':-0.20, 'max':-0.10}, 'talent': None, 'agility': {'min':-0.25, 'max':-0.15}},
        'Fighter':     {'strength': {'min':0.10, 'max':0.15}, 'intelligence': {'min':-0.20, 'max':-0.15}, 'talent': None, 'agility': {'min':-0.20, 'max':-0.15}},
        'Pikeman':     {'strength': {'min':0.10, 'max':0.15}, 'intelligence': {'min':-0.20, 'max':-0.15}, 'talent': None, 'agility': {'min':-0.25, 'max':-0.15}},
        'Archer':      {'strength': {'min':-0.25, 'max':-0.15}, 'intelligence': {'min':-0.20, 'max':-0.10}, 'talent': None, 'agility': {'min':0.15, 'max':0.25}},
        'Knight':      {'strength': {'min':0.05, 'max':0.15}, 'intelligence': {'min':-0.15, 'max':-0.10}, 'talent': {'min':0.05, 'max':0.10}, 'agility': {'min':-0.25, 'max':-0.15}},
        'Atalanta':    {'strength': {'min':-0.20, 'max':-0.15}, 'intelligence': {'min':-0.20, 'max':-0.10}, 'talent': None, 'agility': {'min':0.15, 'max':0.25}},
        'Priestess':   {'strength': {'min':-0.25, 'max':-0.20}, 'intelligence': {'min':0.15, 'max':0.20}, 'talent': {'min':-0.15, 'max':-0.10}, 'agility': {'min':-0.20, 'max':-0.15}},
        'Mage':        {'strength': {'min':-0.25, 'max':-0.20}, 'intelligence': {'min':0.15, 'max':0.25}, 'talent': {'min':-0.15, 'max':-0.10}, 'agility': {'min':-0.20, 'max':-0.15}},
        'Shaman':      {'strength': {'min':-0.25, 'max':-0.20}, 'intelligence': {'min':0.15, 'max':0.25}, 'talent': {'min':-0.15, 'max':-0.10}, 'agility': {'min':-0.20, 'max':-0.15}},
        'Assassin':    {'strength': {'min':0.05, 'max':0.15}, 'intelligence': {'min':-0.20, 'max':-0.10}, 'talent': None, 'agility': {'min':-0.20, 'max':-0.15}},
        'Guerriera':   {'strength': {'min':0.05, 'max':0.15}, 'intelligence': {'min':-0.20, 'max':-0.10}, 'talent': None, 'agility': {'min':-0.20, 'max':-0.15}}
    }

    req = itm.get('requirements') or {}
    # spec may be passed in via function argument - attempt to read it from itm['_spec'] or from a parameter
    # (we expect caller to supply spec parameter when needed). We'll check `itm.get('_spec')` first.
    spec_to_apply = spec or (itm.get('_spec') if isinstance(itm, dict) else None)
    itm['_spec'] = spec_to_apply
    if spec_to_apply and spec_to_apply in SPEC_MODS:
        mods = SPEC_MODS[spec_to_apply]
        for k in ['level','strength','intelligence','talent','agility']:
            if k not in req:
                continue
            if k == 'level':
                continue
            if mods.get(k) is None:
                continue
            pmin = mods[k]['min']; pmax = mods[k]['max']
            rng = _extract_min_max(req[k])
            if rng is None:
                continue
            mn, mx = rng
            low = math.ceil(mn * (1 + pmin))
            high = math.ceil(mx * (1 + pmax))
            req[k] = {'min': {'min': float(min(low, high))}, 'max': {'min': float(max(low, high))}}
    itm['requirements'] = req
    # Apply aging to stats if requested
    try:
        aging_levels = int(aging or 0)
    except Exception:
        aging_levels = 0

    if aging_levels > 0:
        import math
        stats = itm.get('stats') or {}
        # armor/robe: defense +5% per level (floor each step), absorption +0.5 per lvl 1-9, +1.0 per lvl 10+
        # For aging rules prefer annotated category if present
        sub = (itm.get('_category') or itm.get('subCategory') or '').lower()
        isArmorOrRobe = sub in ['armaduras', 'roupoes']
        isShield = sub in ['escudos']
        isOrbital = sub in ['orbitais']

        def apply_range_floor(src, levels, pct_per_level=0.05):
            rng = _extract_min_max(src)
            if rng is None:
                return src
            mn, mx = rng
            for lvl in range(levels):
                mn = math.floor(mn * (1 + pct_per_level))
                mx = math.floor(mx * (1 + pct_per_level))
            return {'min': {'min': float(mn)}, 'max': {'min': float(mx)}}

        def apply_absorption(src, levels, per_level_small=0.5, per_level_big=1.0):
            rng = _extract_min_max(src)
            if rng is None:
                return src
            mn, mx = rng
            for lvl in range(1, levels+1):
                add = per_level_small if lvl <= 9 else per_level_big
                mn += add
                mx += add
                mn = round(mn, 1)
                mx = round(mx, 1)
            return {'min': {'min': float(mn)}, 'max': {'min': float(mx)}}

        if isArmorOrRobe:
            if 'defense' in stats:
                stats['defense'] = apply_range_floor(stats['defense'], aging_levels, pct_per_level=0.05)
            # handle absorption numeric companion
            if 'absorption' in stats or 'absorption_max' in stats:
                if isinstance(stats.get('absorption'), (int, float)) or isinstance(stats.get('absorption_max'), (int, float)):
                    aMin = float(stats.get('absorption') or 0)
                    aMax = float(stats.get('absorption_max') or aMin)
                    stats['absorption'] = {'min': {'min': aMin}, 'max': {'min': aMax}}
                    if 'absorption_max' in stats:
                        del stats['absorption_max']
                stats['absorption'] = apply_absorption(stats.get('absorption'), aging_levels, per_level_small=0.5, per_level_big=1.0)

        if isShield:
            # shields: block +0.5 per level, absorption +0.2 per level (1-9) then +0.4 (10+)
            if 'block' in stats:
                rng = _extract_min_max(stats['block'])
                if rng is not None:
                    mn, mx = rng
                    for lvl in range(aging_levels):
                        mn = mn + 0.5
                        mx = mx + 0.5
                    # final block should be floored to integer per validated examples
                    stats['block'] = {'min': {'min': float(math.floor(mn))}, 'max': {'min': float(math.floor(mx))}}
            if 'absorption' in stats or 'absorption_max' in stats:
                if isinstance(stats.get('absorption'), (int, float)) or isinstance(stats.get('absorption_max'), (int, float)):
                    aMin = float(stats.get('absorption') or 0)
                    aMax = float(stats.get('absorption_max') or aMin)
                    stats['absorption'] = {'min': {'min': aMin}, 'max': {'min': aMax}}
                    if 'absorption_max' in stats:
                        del stats['absorption_max']
                stats['absorption'] = apply_absorption(stats.get('absorption'), aging_levels, per_level_small=0.2, per_level_big=0.4)

        if isOrbital:
            # orbitals: defense +10% per level, absorption +0.5 per level (1-9) then +1.0 (10+)
            if 'defense' in stats:
                stats['defense'] = apply_range_floor(stats['defense'], aging_levels, pct_per_level=0.10)
            if 'absorption' in stats or 'absorption_max' in stats:
                if isinstance(stats.get('absorption'), (int, float)) or isinstance(stats.get('absorption_max'), (int, float)):
                    aMin = float(stats.get('absorption') or 0)
                    aMax = float(stats.get('absorption_max') or aMin)
                    stats['absorption'] = {'min': {'min': aMin}, 'max': {'min': aMax}}
                    if 'absorption_max' in stats:
                        del stats['absorption_max']
                stats['absorption'] = apply_absorption(stats.get('absorption'), aging_levels, per_level_small=0.5, per_level_big=1.0)

        itm['stats'] = stats

    return itm
