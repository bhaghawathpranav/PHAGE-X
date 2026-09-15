import numpy as np

from ml.train import _calibration_report, _host_bootstrap_intervals


def test_calibration_report_accounts_for_every_prediction():
    report = _calibration_report(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]))
    assert sum(item["count"] for item in report["bins"]) == 4
    assert 0 <= report["expected_calibration_error"] <= 1


def test_host_bootstrap_confidence_intervals_are_bounded():
    labels = np.array([0, 1, 0, 1, 0, 1])
    scores = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    hosts = np.array(["a", "a", "b", "b", "c", "c"])
    result = _host_bootstrap_intervals(labels, scores, hosts, repeats=20)
    assert result["roc_auc"]["lower_95"] <= result["roc_auc"]["upper_95"]
