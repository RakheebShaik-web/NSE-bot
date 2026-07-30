from optimize_strategy import candidate_configs, selection_score


def test_candidate_grid_is_bounded():
    base = {"regime": {}, "weights": {}}
    candidates = candidate_configs(base)
    assert len(candidates) == 72
    assert len({c["candidate"] for c in candidates}) == 72


def test_selection_score_rejects_sparse_trials():
    assert selection_score({"trades": 20, "max_dd": -0.1, "sharpe": 3, "return": 2}) == -999
