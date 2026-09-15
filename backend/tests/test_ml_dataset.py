import numpy as np

from ml.dataset import PairDataset, grouped_three_way_split, top_k_recall


def test_grouped_split_has_no_host_leakage():
    hosts = np.repeat([f"host-{i}" for i in range(20)], 4)
    dataset = PairDataset(
        X=np.zeros((80, 11), dtype=np.float32),
        y=np.tile([0, 1, 0, 0], 20),
        hosts=hosts,
        phages=np.tile(["a", "b", "c", "d"], 20),
    )
    train, validation, test = grouped_three_way_split(dataset)
    assert not set(hosts[train]) & set(hosts[validation])
    assert not set(hosts[train]) & set(hosts[test])
    assert not set(hosts[validation]) & set(hosts[test])


def test_top_k_recall_ignores_hosts_without_positive_labels():
    labels = np.array([0, 1, 0, 0, 0, 0])
    probabilities = np.array([0.8, 0.7, 0.1, 0.9, 0.8, 0.7])
    hosts = np.array(["a", "a", "a", "b", "b", "b"])
    assert top_k_recall(labels, probabilities, hosts, 2) == 1.0

