from utils.metrics import f1_score


def test_f1_score_basic():
    assert f1_score(1.0, 1.0) == 1.0
    assert f1_score(0.5, 0.5) == 0.5
    assert f1_score(0.0, 0.5) == 0.0
