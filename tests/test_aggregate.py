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
    assert out['requirements']['strength'] == [120, 136]
    # agility should come from boots (spec Archer doesn't reduce agility here)
    assert out['requirements']['agility'] == [104, 113]
