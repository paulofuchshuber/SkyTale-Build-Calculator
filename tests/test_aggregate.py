from utils.aggregate import aggregate_by_assets
from utils.aggregate import apply_rarity_and_spec

# helper to create fake item with requirement
def make_item_require(req):
    return { 'stats': {}, 'requirements': req }

def test_range_plus_range_strength():
    a = make_item_require({'strength': {'min': {'min': 30}, 'max': {'min': 34}}})
    b = make_item_require({'strength': {'min': {'min': 181}, 'max': {'min': 190}}})
    out = aggregate_by_assets([a,b])
    assert out['requirements']['strength'] == [181,190]

def test_single_plus_range_talent_inside():
    # talent: 50 + (45-56) => expect [50,56]
    a = make_item_require({'talent': 50})
    b = make_item_require({'talent': {'min': {'min':45}, 'max': {'min':56}}})
    out = aggregate_by_assets([a,b])
    assert out['requirements']['talent'] == [50,56]

def test_single_plus_range_talent_above():
    # talent: 90 + (45-56) => expect 90
    a = make_item_require({'talent': 90})
    b = make_item_require({'talent': {'min': {'min':45}, 'max': {'min':56}}})
    out = aggregate_by_assets([a,b])
    assert out['requirements']['talent'] == 90

def test_single_plus_range_talent_below():
    # talent: 20 + (45-56) => expect [45,56]
    a = make_item_require({'talent': 20})
    b = make_item_require({'talent': {'min': {'min':45}, 'max': {'min':56}}})
    out = aggregate_by_assets([a,b])
    assert out['requirements']['talent'] == [45,56]

def test_stats_sum_min_max():
    # stats hp: (15-18) + (18-24) => (33-42)
    a = { 'stats': { 'hp': {'min': {'min':15}, 'max': {'min':18}} }, 'requirements': {} }
    b = { 'stats': { 'hp': {'min': {'min':18}, 'max': {'min':24}} }, 'requirements': {} }
    out = aggregate_by_assets([a,b])
    assert out['stats']['hp'] == [33,42]


def test_example_armor_boots_rarity_spec():
    # Armor (normal, Archer)
    armor = {
        'subCategory': 'armaduras',
        'stats': {
            'absorption': {'min': {'min': 9.2}, 'max': {'min': 9.6}},
            'defense': {'min': {'min': 200}, 'max': {'min': 230}}
        },
        'requirements': {
            'level': 65,
            'strength': {'min': {'min': 120}, 'max': {'min': 136}},
            'talent': 70
        }
    }
    # Boots (rare, Archer)
    boots = {
        'subCategory': 'botas',
        'stats': {
            'absorption': {'min': {'min': 7.7}, 'max': {'min': 8.0}},
            'defense': {'min': {'min': 125}, 'max': {'min': 135}}
        },
        'requirements': {
            'level': 80,
            'strength': {'min': {'min': 60}, 'max': {'min': 68}},
            'agility': {'min': {'min': 104}, 'max': {'min': 113}}
        }
    }

    a1 = apply_rarity_and_spec(armor, rarity='normal', spec='Archer')
    b1 = apply_rarity_and_spec(boots, rarity='rare', spec='Archer')
    out = aggregate_by_assets([a1, b1])

    # absorption: 9.2-9.6 + (7.7-8.0 +1 from rare boots) => 17.9 - 18.6
    assert out['stats']['absorption'] == [17.9, 18.6]
    # defense: 200-230 + (125-135 +10 from rare boots) => 335 - 375
    assert out['stats']['defense'] == [335, 375]
    # requirements: strength should be dominated by armor (120-136)
    # requirements: strength after Archer spec applied to armor
    assert out['requirements']['strength'] == [90, 116]
    # agility should come from boots with Archer spec (increased)
    assert out['requirements']['agility'] == [120, 142]


def make_item_stats(def_val, abs_val):
    return {
        'subCategory': 'armaduras',
        'stats': {
            'defense': {'min': {'min': def_val}, 'max': {'min': def_val}},
            'absorption': abs_val,
            'absorption_max': abs_val
        },
        'requirements': {}
    }

def test_armor_aging_examples():
    base = make_item_stats(120, 5.3)
    a5 = apply_rarity_and_spec(base, rarity='normal', spec=None, aging=5)
    out5 = aggregate_by_assets([a5])
    assert out5['stats']['defense'] == 151
    assert out5['stats']['absorption'] == 7.8

    a9 = apply_rarity_and_spec(base, rarity='normal', spec=None, aging=9)
    out9 = aggregate_by_assets([a9])
    assert out9['stats']['defense'] == 181
    assert out9['stats']['absorption'] == 9.8

    a12 = apply_rarity_and_spec(base, rarity='normal', spec=None, aging=12)
    out12 = aggregate_by_assets([a12])
    assert out12['stats']['defense'] == 208
    assert out12['stats']['absorption'] == 12.8

    a15 = apply_rarity_and_spec(base, rarity='normal', spec=None, aging=15)
    out15 = aggregate_by_assets([a15])
    assert out15['stats']['defense'] == 239
    assert out15['stats']['absorption'] == 15.8


def make_shield(block_val, abs_val):
    return {
        'subCategory': 'escudos',
        'stats': {
            'block': {'min': {'min': block_val}, 'max': {'min': block_val}},
            'absorption': abs_val,
            'absorption_max': abs_val
        },
        'requirements': {}
    }

def make_orbital(def_val, abs_val):
    return {
        'subCategory': 'orbitais',
        'stats': {
            'defense': {'min': {'min': def_val}, 'max': {'min': def_val}},
            'absorption': abs_val,
            'absorption_max': abs_val
        },
        'requirements': {}
    }

def test_shield_and_orbital_aging_examples():
    shield = make_shield(20, 9.4)
    s5 = apply_rarity_and_spec(shield, aging=5)
    out5 = aggregate_by_assets([s5])
    assert out5['stats']['block'] == 22
    assert out5['stats']['absorption'] == 10.4

    s7 = apply_rarity_and_spec(shield, aging=7)
    out7 = aggregate_by_assets([s7])
    assert out7['stats']['block'] == 23
    assert out7['stats']['absorption'] == 10.8

    s12 = apply_rarity_and_spec(shield, aging=12)
    out12 = aggregate_by_assets([s12])
    assert out12['stats']['block'] == 26
    assert out12['stats']['absorption'] == 12.4

    s15 = apply_rarity_and_spec(shield, aging=15)
    out15 = aggregate_by_assets([s15])
    assert out15['stats']['block'] == 27
    assert out15['stats']['absorption'] == 13.6

    orb = make_orbital(132, 5.7)
    o5 = apply_rarity_and_spec(orb, aging=5)
    o5r = aggregate_by_assets([o5])
    assert o5r['stats']['defense'] == 210
    assert o5r['stats']['absorption'] == 8.2

    o7 = apply_rarity_and_spec(orb, aging=7)
    o7r = aggregate_by_assets([o7])
    assert o7r['stats']['defense'] == 254
    assert o7r['stats']['absorption'] == 9.2

    o12 = apply_rarity_and_spec(orb, aging=12)
    o12r = aggregate_by_assets([o12])
    assert o12r['stats']['defense'] == 405
    assert o12r['stats']['absorption'] == 13.2

    o15 = apply_rarity_and_spec(orb, aging=15)
    o15r = aggregate_by_assets([o15])
    assert o15r['stats']['defense'] == 537
    assert o15r['stats']['absorption'] == 16.2


def test_final_requirements_strength_range():
    # Scenario from user: three items with overlapping strength ranges
    spear = {
        'subCategory': 'lancas',
        'stats': {},
        'requirements': {'level': 100, 'strength': {'min': {'min':60}, 'max': {'min':68}}, 'talent': 90, 'agility': {'min': {'min':161}, 'max': {'min':175}}}
    }
    armor = {
        'subCategory': 'armaduras',
        'stats': {},
        'requirements': {'level': 43, 'strength': {'min': {'min':82}, 'max': {'min':87}}, 'talent': 62}
    }
    shield = {
        'subCategory': 'escudos',
        'stats': {},
        'requirements': {'level': 55, 'strength': {'min': {'min':84}, 'max': {'min':90}}, 'talent': 56}
    }

    a1 = apply_rarity_and_spec(spear, rarity='legendary', spec='Archer')
    a2 = apply_rarity_and_spec(armor, rarity='legendary', spec='Atalanta', aging=15)
    a3 = apply_rarity_and_spec(shield, rarity='legendary', spec='Atalanta', aging=15)
    out = aggregate_by_assets([a1, a2, a3])
    # strength should be the dominating range after spec mods -> [68,77]
    assert out['requirements']['strength'] == [68, 77]
