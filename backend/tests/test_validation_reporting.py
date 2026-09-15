import numpy as np

from ml.train import _binary_metrics, _calibration_report, _host_bootstrap_intervals, _validation_threshold


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


def test_validation_threshold_and_binary_metrics_report_confusion_counts():
    labels = np.array([0, 0, 0, 1, 1, 1])
    scores = np.array([0.05, 0.15, 0.35, 0.45, 0.75, 0.95])
    threshold = _validation_threshold(labels, scores)
    result = _binary_metrics(labels, scores, threshold)
    assert 0 <= threshold <= 1
    assert result["true_negatives"] + result["false_positives"] + result["false_negatives"] + result["true_positives"] == len(labels)
    assert 0 <= result["f1"] <= 1
    assert 0 <= result["balanced_accuracy"] <= 1
