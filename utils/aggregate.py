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


def aggregate_by_assets(selected_items):
    # selected_items: list of item dicts
    # aggregate stats: sum of mins and sum of maxs per stat key
    stats_acc = {}
    # requirements: collect ranges for keys
    req_keys = ['level','strength','intelligence','talent','agility']
    req_ranges = {k: [] for k in req_keys}

    for item in selected_items:
        st = item.get('stats', {}) or {}
        # handle paired keys like 'absorption' + 'absorption_max' or 'attackRating' + 'attackRating_max'
        processed = set()
        for k in list(st.keys()):
            if k in processed:
                continue
            # skip keys that are *_max by themselves
            if k.endswith('_max'):
                continue
            companion = k + '_max'
            if companion in st and isinstance(st[k], (int, float)) and isinstance(st[companion], (int, float)):
                mn = float(st[k])
                mx = float(st[companion])
                processed.add(companion)
            else:
                rng = _extract_min_max(st[k])
                if rng is None:
                    continue
                mn, mx = rng
            # accumulate as floats when necessary
            if k not in stats_acc:
                stats_acc[k] = [0.0, 0.0]
            stats_acc[k][0] += float(mn)
            stats_acc[k][1] += float(mx)

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

    # build stats result: if min==max show single int/float, else list
    stats_out = {}
    for k, (smin, smax) in stats_acc.items():
        # don't expose keys with '_max'
        if k.endswith('_max'):
            continue
        # if both are integers (no fractional part), return ints; else round absorption-like to 1 decimal
        def is_intish(x):
            return abs(x - int(x)) < 1e-9

        if abs(smin - smax) < 1e-9:
            # single value
            if is_intish(smin):
                stats_out[k] = int(smin)
            else:
                stats_out[k] = round(smin, 1)
        else:
            if is_intish(smin) and is_intish(smax):
                stats_out[k] = [int(smin), int(smax)]
            else:
                stats_out[k] = [round(smin, 1), round(smax, 1)]

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

    # helper to add bonus to a numeric range (min,max)
    def add_bonus_to_range(src, add):
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
    # attackRating
    if atkRatingBonus and 'attackRating' in stats:
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
