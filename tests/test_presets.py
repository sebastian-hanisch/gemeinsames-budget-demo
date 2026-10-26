"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, keiner auf einem Reglerrand und keiner, der durch eine einzelne Regleränderung vom Standard entsteht."""

import gmb_constants as C
import gmb_evaluation as ev
import gmb_presets as P

FIRST = "Zwei Lager: gierig oder gleiche Anteile"
BOUNDS = {"n": (C.N_MIN, C.N_MAX), "m": (C.M_MIN, C.M_MAX), "budget": (C.BUDGET_MIN, C.BUDGET_MAX), "group": (C.GROUP_MIN, C.GROUP_MAX),
          "own": (C.OWN_MIN, C.OWN_MAX), "cross": (C.CROSS_MIN, C.CROSS_MAX), "seed": (0, C.SEED_MAX)}


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, p in C.PRESETS.items():
        for key, (lo, hi) in BOUNDS.items():
            assert lo <= p[key] <= hi, (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[FIRST]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_preset_sits_on_a_slider_bound():
    for name, preset in C.PRESETS.items():
        for key, (lo, hi) in BOUNDS.items():
            assert preset[key] not in (lo, hi), (name, key)


def test_no_single_change_of_the_default_produces_another_preset():
    default = C.PRESETS[FIRST]
    for name, p in C.PRESETS.items():
        if name != FIRST:
            assert sum(1 for k in p if p[k] != default[k]) >= 2, name


def test_presets_are_pairwise_different():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_the_two_lager_have_a_minority_project_each_side():
    for m in range(C.M_MIN, C.M_MAX + 1):
        from gmb_scenario import make_instance
        inst = make_instance(C.N_MIN, m, C.BUDGET_MIN, C.GROUP_MAX, C.OWN_MIN, C.CROSS_MAX, 1)
        assert int((inst.own == 1).sum()) == m // 2 and int((inst.own == 0).sum()) == m - m // 2
        assert int((inst.group == 1).sum()) >= 1 and int((inst.group == 0).sum()) >= 1
