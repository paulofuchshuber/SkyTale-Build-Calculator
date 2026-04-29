from utils.aggregate import calc_stat_points

# Os 99 pontos base são os stats iniciais da classe (STATS_BASE) — já alocados.
# calc_stat_points retorna apenas os pontos DISTRIBUÍVEIS ganhos ao subir de nível.

# ─── level 1 (base) ───────────────────────────────────────────────────────────

def test_level_1_no_distributable_points():
    assert calc_stat_points(1) == 0

# ─── antes do primeiro bônus (levels 2-29: +5/level) ─────────────────────────

def test_level_2():
    assert calc_stat_points(2) == 5

def test_level_10():
    assert calc_stat_points(10) == 9 * 5       # 45

def test_level_29_no_bonus_yet():
    assert calc_stat_points(29) == 28 * 5      # 140

# ─── level 30: primeiro bônus (+5 pontual) ────────────────────────────────────

def test_level_30():
    assert calc_stat_points(30) == 29 * 5 + 5  # 150

def test_level_30_increment_from_29():
    assert calc_stat_points(30) - calc_stat_points(29) == 5 + 5  # +5 nível + +5 bônus

# ─── levels 31-69: +5/level ───────────────────────────────────────────────────

def test_level_50():
    assert calc_stat_points(50) == 49 * 5 + 5  # 250

def test_level_69_before_second_bonus():
    assert calc_stat_points(69) == 68 * 5 + 5  # 345

# ─── level 70: segundo bônus ──────────────────────────────────────────────────

def test_level_70():
    assert calc_stat_points(70) == 69 * 5 + 5 + 5  # 355

def test_level_70_increment_from_69():
    assert calc_stat_points(70) - calc_stat_points(69) == 5 + 5  # +5 nível + +5 bônus

# ─── levels 71-79: +5/level ───────────────────────────────────────────────────

def test_level_79():
    assert calc_stat_points(79) == 78 * 5 + 10  # 400

# ─── level 80: taxa muda para +7, mais bônus pontual ─────────────────────────

def test_level_80():
    # 78 levels a +5, 1 level a +7, mais 3 bônus (30, 70, 80)
    assert calc_stat_points(80) == 78 * 5 + 1 * 7 + 15  # 412

def test_level_80_increment_from_79():
    assert calc_stat_points(80) - calc_stat_points(79) == 7 + 5  # +7 nível + +5 bônus

# ─── levels 81-89: +7/level ───────────────────────────────────────────────────

def test_level_81():
    assert calc_stat_points(81) == calc_stat_points(80) + 7  # 419

def test_level_89():
    assert calc_stat_points(89) == 78 * 5 + 10 * 7 + 15  # 475

def test_levels_81_to_89_increment():
    for lvl in range(81, 90):
        assert calc_stat_points(lvl) - calc_stat_points(lvl - 1) == 7

# ─── level 90: taxa muda para +10 ────────────────────────────────────────────

def test_level_90():
    assert calc_stat_points(90) == 78 * 5 + 10 * 7 + 1 * 10 + 15  # 485

def test_level_90_increment_from_89():
    assert calc_stat_points(90) - calc_stat_points(89) == 10

# ─── levels 91+: +10/level ────────────────────────────────────────────────────

def test_levels_90_to_100_increment():
    for lvl in range(90, 101):
        assert calc_stat_points(lvl) - calc_stat_points(lvl - 1) == 10

def test_level_100():
    assert calc_stat_points(100) == 585

def test_level_150_max():
    assert calc_stat_points(150) == 1085

# ─── boundary / clamping ──────────────────────────────────────────────────────

def test_level_0_clamped_to_1():
    assert calc_stat_points(0) == calc_stat_points(1)

def test_level_151_clamped_to_150():
    assert calc_stat_points(151) == calc_stat_points(150)

def test_float_level_truncated():
    assert calc_stat_points(30.9) == calc_stat_points(30)
