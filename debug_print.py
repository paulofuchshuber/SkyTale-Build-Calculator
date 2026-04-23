from utils.aggregate import aggregate_by_assets, apply_rarity_and_spec

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
print('armor requirements after apply:', a1.get('requirements'))
print('boots requirements after apply:', b1.get('requirements'))
print('combined requirements:', out['requirements'])
print('combined stats:', out['stats'])
