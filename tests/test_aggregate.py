from utils.aggregate import aggregate_by_assets, apply_rarity_and_spec

# ─── helpers ──────────────────────────────────────────────────────────────────

def make_item(cat='armaduras', stats=None, reqs=None, spec=None):
    return {'_category': cat, 'stats': stats or {}, 'requirements': reqs or {},
            **(({'spec': spec}) if spec else {})}

def nested(mn, mx):
    return {'min': {'min': mn}, 'max': {'min': mx}}

def agg1(item, **kw):
    return aggregate_by_assets([apply_rarity_and_spec(item, **kw)])


# ─── requisitos: agregação (comportamento existente) ──────────────────────────

def test_range_plus_range_strength():
    a = make_item(reqs={'strength': nested(30, 34)})
    b = make_item(reqs={'strength': nested(181, 190)})
    out = aggregate_by_assets([a, b])
    assert out['requirements']['strength'] == [181, 190]

def test_single_plus_range_talent_inside():
    a = make_item(reqs={'talent': 50})
    b = make_item(reqs={'talent': nested(45, 56)})
    out = aggregate_by_assets([a, b])
    assert out['requirements']['talent'] == [50, 56]

def test_single_plus_range_talent_above():
    a = make_item(reqs={'talent': 90})
    b = make_item(reqs={'talent': nested(45, 56)})
    out = aggregate_by_assets([a, b])
    assert out['requirements']['talent'] == 90

def test_single_plus_range_talent_below():
    a = make_item(reqs={'talent': 20})
    b = make_item(reqs={'talent': nested(45, 56)})
    out = aggregate_by_assets([a, b])
    assert out['requirements']['talent'] == [45, 56]

def test_stats_sum_min_max():
    a = make_item(stats={'hp': nested(15, 18)})
    b = make_item(stats={'hp': nested(18, 24)})
    out = aggregate_by_assets([a, b])
    assert out['stats']['hp'] == [33, 42]


# ─── raridade: armas ──────────────────────────────────────────────────────────

def test_weapon_normal_no_rarity_bonus():
    sword = make_item('espadas', stats={'attackPower': nested(100, 150)})
    out = agg1(sword, rarity='normal')
    assert out['stats']['attackPower'] == [100, 150]

def test_weapon_epic_attack_bonus():
    sword = make_item('espadas', stats={
        'attackPower': nested(100, 150),
        'attackRating': nested(30, 40),
    })
    out = agg1(sword, rarity='epic')
    assert out['stats']['attackPower'] == [108, 158]
    assert out['stats']['attackRating'] == [50, 60]

def test_weapon_legendary_attack_bonus():
    axe = make_item('machados', stats={
        'attackPower': nested(80, 120),
        'attackRating': nested(20, 30),
    })
    out = agg1(axe, rarity='legendary')
    assert out['stats']['attackPower'] == [92, 132]
    assert out['stats']['attackRating'] == [50, 60]


# ─── raridade: armaduras e roupões ────────────────────────────────────────────

def test_armor_rare_defense_absorption():
    armor = make_item('armaduras', stats={'defense': nested(200, 250), 'absorption': 8.0, 'absorption_max': 10.0})
    out = agg1(armor, rarity='rare')
    assert out['stats']['defense'] == [230, 280]
    assert out['stats']['absorption'] == [9, 11]

def test_robe_legendary_defense_absorption():
    robe = make_item('roupoes', stats={'defense': nested(200, 250), 'absorption': 8.0, 'absorption_max': 10.0})
    out = agg1(robe, rarity='legendary')
    assert out['stats']['defense'] == [290, 340]
    assert out['stats']['absorption'] == [11, 13]


# ─── raridade: botas e luvas ──────────────────────────────────────────────────

def test_boots_epic_defense_absorption():
    boots = make_item('botas', stats={'defense': nested(80, 100), 'absorption': 4.0, 'absorption_max': 5.0})
    out = agg1(boots, rarity='epic')
    assert out['stats']['defense'] == [100, 120]
    assert out['stats']['absorption'] == [6, 7]

def test_gloves_legendary_defense_absorption():
    gloves = make_item('luvas', stats={'defense': nested(60, 80), 'absorption': 3.0, 'absorption_max': 4.0})
    out = agg1(gloves, rarity='legendary')
    assert out['stats']['defense'] == [90, 110]
    assert out['stats']['absorption'] == [6, 7]


# ─── raridade: escudo, bracelete, orbital ─────────────────────────────────────

def test_shield_rare_absorption_only():
    shield = make_item('escudos', stats={'absorption': 5.0, 'absorption_max': 7.0})
    out = agg1(shield, rarity='rare')
    assert out['stats']['absorption'] == [6, 8]

def test_bracelet_legendary_attack_rating_only():
    brac = make_item('braceletes', stats={'attackRating': 20, 'attackRating_max': 20})
    out = agg1(brac, rarity='legendary')
    assert out['stats']['attackRating'] == 50

def test_orbital_legendary_no_rarity_bonus():
    # orbitais não recebem bônus de raridade
    orb = make_item('orbitais', stats={'defense': nested(100, 120), 'absorption': 5.0, 'absorption_max': 5.0})
    out = agg1(orb, rarity='legendary')
    assert out['stats']['defense'] == [100, 120]
    assert out['stats']['absorption'] == 5


# ─── spec: modificadores de requisitos ───────────────────────────────────────

def test_spec_mechanician():
    item = make_item(reqs={'strength': 100, 'intelligence': 50, 'talent': 80, 'agility': 60})
    out = agg1(item, spec='Mechanician')
    # ceil(100*1.10) = 111 (floating-point: 100*1.10 > 110)
    assert out['requirements']['strength'] == [105, 111]
    assert out['requirements']['intelligence'] == [40, 45]
    assert out['requirements']['talent'] == 80      # Mechanician: talent = None (sem alteração)
    assert out['requirements']['agility'] == [45, 51]

def test_spec_knight_has_talent_modifier():
    item = make_item(reqs={'strength': 100, 'intelligence': 50, 'talent': 80, 'agility': 40})
    out = agg1(item, spec='Knight')
    assert out['requirements']['strength'] == [105, 115]
    assert out['requirements']['intelligence'] == [43, 45]
    assert out['requirements']['talent'] == [84, 88]
    assert out['requirements']['agility'] == [30, 34]

def test_spec_mage():
    item = make_item('varinhas', reqs={'strength': 40, 'intelligence': 60, 'talent': 70, 'agility': 30})
    out = agg1(item, spec='Mage')
    assert out['requirements']['strength'] == [30, 32]
    assert out['requirements']['intelligence'] == [69, 75]
    assert out['requirements']['talent'] == [60, 63]
    assert out['requirements']['agility'] == [24, 26]

def test_spec_atalanta():
    item = make_item('arcos', reqs={'strength': 60, 'talent': 50, 'agility': 40})
    out = agg1(item, spec='Atalanta')
    assert out['requirements']['strength'] == [48, 51]
    assert out['requirements']['talent'] == 50      # Atalanta: talent = None
    assert out['requirements']['agility'] == [46, 50]

def test_spec_pikeman():
    item = make_item('lancas', reqs={'strength': 80, 'intelligence': 30})
    out = agg1(item, spec='Pikeman')
    assert out['requirements']['strength'] == [88, 92]
    assert out['requirements']['intelligence'] == [24, 26]

def test_spec_none_keeps_scalar():
    item = make_item(reqs={'strength': 95, 'level': 60})
    out = agg1(item, spec=None)
    assert out['requirements']['strength'] == 95
    assert out['requirements']['level'] == 60


# ─── aging ────────────────────────────────────────────────────────────────────

def test_example_armor_boots_rarity_spec():
    armor = make_item('armaduras', stats={'absorption': nested(9.2, 9.6), 'defense': nested(200, 230)},
                      reqs={'level': 65, 'strength': nested(120, 136), 'talent': 70})
    boots = make_item('botas', stats={'absorption': nested(7.7, 8.0), 'defense': nested(125, 135)},
                      reqs={'level': 80, 'strength': nested(60, 68), 'agility': nested(104, 113)})
    a1 = apply_rarity_and_spec(armor, rarity='normal', spec='Archer')
    b1 = apply_rarity_and_spec(boots, rarity='rare', spec='Archer')
    out = aggregate_by_assets([a1, b1])
    assert out['stats']['absorption'] == [17.9, 18.6]
    assert out['stats']['defense'] == [335, 375]
    assert out['requirements']['strength'] == [90, 116]
    assert out['requirements']['agility'] == [120, 142]

def test_armor_aging_examples():
    def make_a(d, a): return make_item('armaduras', stats={'defense': nested(d, d), 'absorption': a, 'absorption_max': a})
    base = make_a(120, 5.3)
    assert agg1(base, aging=5)['stats']['defense'] == 151
    assert agg1(base, aging=5)['stats']['absorption'] == 7.8
    assert agg1(base, aging=9)['stats']['defense'] == 181
    assert agg1(base, aging=9)['stats']['absorption'] == 9.8
    assert agg1(base, aging=12)['stats']['defense'] == 208
    assert agg1(base, aging=12)['stats']['absorption'] == 12.8
    assert agg1(base, aging=15)['stats']['defense'] == 239
    assert agg1(base, aging=15)['stats']['absorption'] == 15.8

def test_armor_aging_boundary_level_10():
    # verifica que absorption muda de +0.5 para +1.0 a partir do nível 10
    base = make_item('armaduras', stats={'defense': nested(100, 100), 'absorption': 3.0, 'absorption_max': 3.0})
    assert agg1(base, aging=10)['stats']['defense'] == 158
    assert agg1(base, aging=10)['stats']['absorption'] == 8.5
    assert agg1(base, aging=11)['stats']['defense'] == 165
    assert agg1(base, aging=11)['stats']['absorption'] == 9.5

def test_shield_and_orbital_aging_examples():
    def make_sh(b, a): return make_item('escudos', stats={'block': nested(b, b), 'absorption': a, 'absorption_max': a})
    shield = make_sh(20, 9.4)
    assert agg1(shield, aging=5)['stats']['block'] == 22
    assert agg1(shield, aging=5)['stats']['absorption'] == 10.4
    assert agg1(shield, aging=7)['stats']['block'] == 23
    assert agg1(shield, aging=7)['stats']['absorption'] == 10.8
    assert agg1(shield, aging=12)['stats']['block'] == 26
    assert agg1(shield, aging=12)['stats']['absorption'] == 12.4
    assert agg1(shield, aging=15)['stats']['block'] == 27
    assert agg1(shield, aging=15)['stats']['absorption'] == 13.6

    def make_orb(d, a): return make_item('orbitais', stats={'defense': nested(d, d), 'absorption': a, 'absorption_max': a})
    orb = make_orb(132, 5.7)
    assert agg1(orb, aging=5)['stats']['defense'] == 210
    assert agg1(orb, aging=5)['stats']['absorption'] == 8.2
    assert agg1(orb, aging=7)['stats']['defense'] == 254
    assert agg1(orb, aging=7)['stats']['absorption'] == 9.2
    assert agg1(orb, aging=12)['stats']['defense'] == 405
    assert agg1(orb, aging=12)['stats']['absorption'] == 13.2
    assert agg1(orb, aging=15)['stats']['defense'] == 537
    assert agg1(orb, aging=15)['stats']['absorption'] == 16.2

def test_weapon_has_no_aging_effect():
    sword = make_item('espadas', stats={'attackPower': nested(100, 150)})
    out = agg1(sword, aging=10)
    assert out['stats']['attackPower'] == [100, 150]


# ─── multi-item: cenários combinados ─────────────────────────────────────────

def test_multi_item_mixed_rarity_spec():
    sword  = make_item('espadas',   stats={'attackPower': nested(100, 140)}, reqs={'strength': 80, 'intelligence': 20})
    armor  = make_item('armaduras', stats={'defense': nested(150, 180), 'absorption': 6.0, 'absorption_max': 8.0},
                       reqs={'strength': 100, 'intelligence': 90})
    out = aggregate_by_assets([
        apply_rarity_and_spec(sword, rarity='epic',  spec='Fighter'),
        apply_rarity_and_spec(armor, rarity='rare',  spec='Mage'),
    ])
    assert out['stats']['attackPower'] == [108, 148]
    assert out['stats']['defense'] == [180, 210]
    assert out['stats']['absorption'] == [7, 9]
    assert out['requirements']['strength'] == [88, 92]      # Fighter sword domina sobre Mage armor
    assert out['requirements']['intelligence'] == [104, 113] # Mage armor domina

def test_final_requirements_strength_range():
    spear = make_item('lancas',   reqs={'level': 100, 'strength': nested(60, 68), 'talent': 90, 'agility': nested(161, 175)})
    armor = make_item('armaduras',reqs={'level': 43,  'strength': nested(82, 87), 'talent': 62})
    shield= make_item('escudos',  reqs={'level': 55,  'strength': nested(84, 90), 'talent': 56})
    out = aggregate_by_assets([
        apply_rarity_and_spec(spear,  rarity='legendary', spec='Archer'),
        apply_rarity_and_spec(armor,  rarity='legendary', spec='Atalanta', aging=15),
        apply_rarity_and_spec(shield, rarity='legendary', spec='Atalanta', aging=15),
    ])
    assert out['requirements']['strength'] == [68, 77]

def test_empty_item_no_effect():
    ring = make_item('aneis')
    out = aggregate_by_assets([ring])
    assert out['stats'].get('defense', '-') == '-'
    assert out['requirements'].get('strength', '-') == '-'

def test_full_build_weapon_armor_shield_boots():
    weapon = make_item('espadas',   stats={'attackPower': nested(120, 160)}, reqs={'strength': 90})
    armor  = make_item('armaduras', stats={'defense': nested(200, 240), 'absorption': 9.0, 'absorption_max': 11.0},
                       reqs={'strength': 110, 'talent': 70})
    shield = make_item('escudos',   stats={'block': nested(30, 30), 'absorption': 8.0, 'absorption_max': 9.0},
                       reqs={'strength': 80})
    boots  = make_item('botas',     stats={'defense': nested(100, 120), 'absorption': 5.0, 'absorption_max': 6.0},
                       reqs={'agility': 60})
    out = aggregate_by_assets([
        apply_rarity_and_spec(weapon, rarity='epic',      spec='Fighter'),
        apply_rarity_and_spec(armor,  rarity='legendary', spec='Fighter', aging=5),
        apply_rarity_and_spec(shield, rarity='epic'),
        apply_rarity_and_spec(boots,  rarity='rare',      spec='Fighter'),
    ])
    # weapon epic: attackPower [128, 168]
    assert out['stats']['attackPower'] == [128, 168]
    # strength req: Fighter mods sobre 90→[100,104], 110→[122,127], 80→shield sem spec → max = [122, 127]
    # ceil(90*1.10)=100 e ceil(110*1.10)=122 por arredondamento float (99.000...01 e 121.000...01)
    assert out['requirements']['strength'] == [122, 127]


# ─── Feature: Bônus por Classe ────────────────────────────────────────────────
# Estes testes falharão até que aggregate_by_assets aceite selected_class.
# Definem o comportamento esperado da nova funcionalidade.

def make_item_with_bonus(cat, stats, reqs, bonuses, primary_class):
    return {'_category': cat, 'stats': stats, 'requirements': reqs,
            'spec': {'bonuses': bonuses, 'primaryClass': primary_class}}

def test_bonus_armor_class_match():
    item = make_item_with_bonus(
        'armaduras',
        {'defense': nested(100, 120), 'absorption': 5.0, 'absorption_max': 7.0},
        {'strength': 80},
        {'defense': {'min': {'min': 5, 'max': 5}, 'max': {'min': 10, 'max': 10}},
         'absorption': 0.1, 'absorption_max': 0.2},
        'Fighter Mechanician',
    )
    out = aggregate_by_assets([item], selected_class='Fighter')
    assert out['stats']['defense'] == [105, 130]
    assert out['stats']['absorption'] == [5.1, 7.2]

def test_bonus_armor_class_no_match():
    item = make_item_with_bonus(
        'armaduras',
        {'defense': nested(100, 120), 'absorption': 5.0, 'absorption_max': 7.0},
        {},
        {'defense': {'min': {'min': 5, 'max': 5}, 'max': {'min': 10, 'max': 10}}},
        'Fighter Mechanician',
    )
    out = aggregate_by_assets([item], selected_class='Mage')
    assert out['stats']['defense'] == [100, 120]

def test_bonus_no_class_selected_keeps_current_behavior():
    # selected_class=None → idêntico ao comportamento atual
    item = make_item_with_bonus(
        'armaduras',
        {'defense': nested(100, 120)},
        {},
        {'defense': {'min': {'min': 5, 'max': 5}, 'max': {'min': 10, 'max': 10}}},
        'Fighter',
    )
    out_new  = aggregate_by_assets([item], selected_class=None)
    out_curr = aggregate_by_assets([make_item('armaduras', stats={'defense': nested(100, 120)})])
    assert out_new['stats']['defense'] == out_curr['stats']['defense']

def test_bonus_weapon_class_match():
    item = make_item_with_bonus(
        'machados',
        {'attackPower': nested(80, 100)},
        {},
        {'attackPower': {'min': {'min': 4, 'max': 4}, 'max': {'min': 4, 'max': 4}}},
        'Mechanician Pikeman',
    )
    out = aggregate_by_assets([item], selected_class='Mechanician')
    assert out['stats']['attackPower'] == [84, 104]

def test_bonus_two_items_only_matching_gets_bonus():
    matching = make_item_with_bonus(
        'armaduras',
        {'defense': nested(100, 100)},
        {},
        {'defense': {'min': {'min': 10, 'max': 10}, 'max': {'min': 10, 'max': 10}}},
        'Fighter',
    )
    non_matching = make_item_with_bonus(
        'roupoes',
        {'defense': nested(50, 50)},
        {},
        {'defense': {'min': {'min': 20, 'max': 20}, 'max': {'min': 20, 'max': 20}}},
        'Mage Priestess',
    )
    out = aggregate_by_assets([matching, non_matching], selected_class='Fighter')
    # matching: 100+10=110 | non_matching: 50 (sem bônus) → total [160, 160] = 160
    assert out['stats']['defense'] == 160

def test_bonus_shield_class_match():
    item = make_item_with_bonus(
        'escudos',
        {'block': nested(20, 20), 'absorption': 9.0, 'absorption_max': 9.0},
        {},
        {'block': 2.0, 'absorption': 0.1, 'absorption_max': 0.3},
        'Knight Fighter',
    )
    out = aggregate_by_assets([item], selected_class='Knight')
    assert out['stats']['block'] == 22
    assert out['stats']['absorption'] == [9.1, 9.3]


# ─── Feature: Bônus — restrição por spec de slot ─────────────────────────────
# O bônus só é aplicado quando o spec do slot == selected_class.
# Bug reportado: spec=Knight + selected_class=Mechanician estava somando bônus.

def test_bonus_spec_mismatch_no_bonus():
    # Bug reportado: Escudo do Vampiro, spec=Knight, selected_class=Mechanician → sem bônus
    shield = make_item_with_bonus(
        'escudos',
        {'defense': nested(174, 192), 'absorption': 9.1, 'absorption_max': 9.4, 'block': 17.0},
        {'level': 80, 'strength': 130, 'talent': 75},
        {'defense': nested(32, 38), 'absorption': 0.9, 'absorption_max': 1.2, 'block': 4.0},
        'Mechanician Fighter Pikeman Archer Knight Atalanta Priestess Magician',
    )
    item = apply_rarity_and_spec(shield, rarity='normal', spec='Knight', aging=0)
    out = aggregate_by_assets([item], selected_class='Mechanician')
    assert out['stats']['defense'] == [174, 192]
    assert out['stats']['absorption'] == [9.1, 9.4]
    assert out['stats']['block'] == 17

def test_bonus_spec_matches_selected_class():
    # spec=Mechanician e selected_class=Mechanician → bônus aplicado
    shield = make_item_with_bonus(
        'escudos',
        {'defense': nested(174, 192), 'absorption': 9.1, 'absorption_max': 9.4, 'block': 17.0},
        {'level': 80, 'strength': 130, 'talent': 75},
        {'defense': nested(32, 38), 'absorption': 0.9, 'absorption_max': 1.2, 'block': 4.0},
        'Mechanician Fighter Pikeman Archer Knight Atalanta Priestess Magician',
    )
    item = apply_rarity_and_spec(shield, rarity='normal', spec='Mechanician', aging=0)
    out = aggregate_by_assets([item], selected_class='Mechanician')
    assert out['stats']['defense'] == [206, 230]   # 174+32=206, 192+38=230
    assert out['stats']['absorption'] == [10, 10.6] # 9.1+0.9=10.0, 9.4+1.2=10.6
    assert out['stats']['block'] == 21              # 17+4=21

def test_bonus_no_slot_spec_uses_primary_class():
    # spec=None → sem restrição de slot, bônus aplica se selected_class in primaryClass
    armor = make_item_with_bonus(
        'armaduras',
        {'defense': nested(100, 120)},
        {},
        {'defense': nested(10, 15)},
        'Fighter Mechanician',
    )
    item = apply_rarity_and_spec(armor, rarity='normal', spec=None, aging=0)
    out = aggregate_by_assets([item], selected_class='Fighter')
    assert out['stats']['defense'] == [110, 135]

def test_bonus_spec_fighter_class_knight_no_bonus():
    # spec=Fighter, selected_class=Knight → spec ≠ class → sem bônus
    armor = make_item_with_bonus(
        'armaduras',
        {'defense': nested(200, 240), 'absorption': 8.0, 'absorption_max': 10.0},
        {},
        {'defense': nested(20, 30), 'absorption': 0.5, 'absorption_max': 0.8},
        'Fighter Knight Mechanician',
    )
    item = apply_rarity_and_spec(armor, rarity='epic', spec='Fighter', aging=0)
    out = aggregate_by_assets([item], selected_class='Knight')
    # epic armor: defense +60, absorption +2; sem bônus
    assert out['stats']['defense'] == [260, 300]
    assert out['stats']['absorption'] == [10, 12]

def test_bonus_spec_and_class_both_knight():
    # spec=Knight e selected_class=Knight → bônus aplicado
    shield = make_item_with_bonus(
        'escudos',
        {'block': nested(20, 20), 'absorption': 8.0, 'absorption_max': 8.0},
        {},
        {'block': 3.0, 'absorption': 0.5, 'absorption_max': 0.5},
        'Knight Fighter Mechanician',
    )
    item = apply_rarity_and_spec(shield, rarity='normal', spec='Knight', aging=0)
    out = aggregate_by_assets([item], selected_class='Knight')
    assert out['stats']['block'] == 23
    assert out['stats']['absorption'] == 8.5

def test_bonus_two_items_spec_only_one_matches_class():
    # Dois itens: armor spec=Fighter classe=Fighter (bônus), shield spec=Knight classe=Fighter (sem bônus)
    armor = make_item_with_bonus(
        'armaduras',
        {'defense': nested(100, 100)},
        {},
        {'defense': nested(10, 10)},
        'Fighter Knight',
    )
    shield = make_item_with_bonus(
        'escudos',
        {'defense': nested(50, 50)},
        {},
        {'defense': nested(20, 20)},
        'Fighter Knight',
    )
    out = aggregate_by_assets([
        apply_rarity_and_spec(armor, rarity='normal', spec='Fighter', aging=0),
        apply_rarity_and_spec(shield, rarity='normal', spec='Knight', aging=0),
    ], selected_class='Fighter')
    # armor: 100+10=110; shield: 50 (sem bônus) → total 160
    assert out['stats']['defense'] == 160
