"""
Tests for SegmentationMetricsByPixels class from batchflow.models.metrics.
Structurally, file consists of two main classes. First one tests metric's output shape, second — its contents.
Main test functions run for almost all metrics values, declared in metrics_dict (exceptions described below).
Test data is pre-defined, it's shape and contents were chosen for reasons of balance between visual simplicity
and test coverage diversity.
"""

import numpy as np
import pytest

from itertools import chain
from batchflow.models.metrics import SegmentationMetricsByPixels

# Dict {metric_alias : metric_names}
metrics_dict = {'tpr' : ['true_positive_rate', 'sensitivity', 'recall'],
                'fpr' : ['false_positive_rate', 'fallout'],
                'fnr' : ['false_negative_rate', 'miss_rate'],
                'tnr' : ['true_negative_rate', 'specificity'],
                'prv' : ['prevalence'],
                'acc' : ['accuracy'], # can't process 'multiclass' parameter and therefore should be tested individualy
                'ppv' : ['positive_predictive_value', 'precision'],
                'fdr' : ['false_discovery_rate'],
                'for' : ['false_omission_rate'],
                'npv' : ['negative_predictive_value'],
                'plr' : ['positive_likelihood_ratio'],
                'nlr' : ['negative_likelihood_ratio'],
                'dor' : ['diagnostics_odds_ratio'],
                'fos' : ['f1_score', 'dice'],
                'jac' : ['jaccard', 'iou']}

metrics_names = list(chain.from_iterable(metrics_dict.values())) # list of all metric names from metrics_dict values
metrics_names.remove('accuracy') # since accuracy is tested separately, it is removed from metrics_names list

batch_size = 2
image_size = 2
num_classes = 3
targets = np.array([0, 1, 2, 2, 0, 0, 1, 1]).reshape(batch_size, image_size, image_size)
labels = np.array([0, 1, 1, 0, 2, 0, 1, 1]).reshape(batch_size, image_size, image_size)
proba = np.eye(num_classes)[labels] #onehots are basically like probas, just with all 0 and a single 1
logits = np.log(proba / (1. - proba)) #logit function gives ±infs on degenerate case of 0s and 1s, but it's okay for sigmoid function

# Wrapper over np.allclose(), that works with np.nan values.
def nanallclose(a, b, atol, rtol):
    if (np.isnan(a) != np.isnan(b)).any():
        return False
    else:
        return np.allclose(np.nan_to_num(a), np.nan_to_num(b), rtol, atol)

class TestShape:
    """
    Checks the shape of return value for all combinations of both types of metrics aggregation and predictions shapes.
    """

    # First param stands for predictions variable, second — for predictions type, third — for axis with class info.
    predictions_params = [(labels, 'labels', None),
                          (proba, 'proba', 3),
                          (logits, 'logits', 3)]

    # First param stands for batch aggregation type, second — for multiclass one, third represents expected output shape.
    aggregation_params = [(None, None, (batch_size, num_classes)),
                          (None, 'micro', (batch_size,)),
                          (None, 'macro', (batch_size,)),
                          ('mean', None, (num_classes,)),
                          ('mean', 'micro', None),
                          ('mean', 'macro', None)]

    @pytest.mark.parametrize('predictions, fmt, axis', predictions_params)
    @pytest.mark.parametrize('batch_agg, multi_agg, exp_shape', aggregation_params)
    def test_shape(self, predictions, fmt, axis, batch_agg, multi_agg, exp_shape):

        metric = SegmentationMetricsByPixels(targets, predictions, fmt, num_classes, axis)
        for metric_name in metrics_names:
            res = metric.evaluate(metrics=metric_name, agg=batch_agg, multiclass=multi_agg)
            res_shape = res.shape if isinstance(res, np.ndarray) else None

            assert res_shape == exp_shape, 'failed on metric {}'.format(metric_name)

    # Individual test params for accuracy — batch-only aggregation param and corresponding expected shapes.
    aggregation_params_accuracy = [(None, (batch_size,)),
                                   ('mean', None)]

    @pytest.mark.parametrize('predictions, fmt, axis', predictions_params)
    @pytest.mark.parametrize('batch_agg, exp_shape', aggregation_params_accuracy)
    def test_shape_accuracy(self, predictions, fmt, axis, batch_agg, exp_shape):

        metric = SegmentationMetricsByPixels(targets, predictions, fmt, num_classes, axis)
        res = metric.evaluate(metrics='accuracy', agg=batch_agg)
        res_shape = res.shape if isinstance(res, np.ndarray) else None

        assert res_shape == exp_shape

class TestResult:
    """
    Checks the contents of return value for all combinations of both types of metrics aggregation.
    """

    # First param stands for batch aggregation type, second — for multiclass one,
    # third represents expected output contents for each type of metrics.
    params = [(None, None, {'tpr' : np.array([1.00, 1.00, 0.00, 0.50, 1.00, 1.00]),
                            'fpr' : np.array([0.33, 0.33, 0.00, 0.00, 0.00, 0.25]),
                            'tnr' : np.array([0.66, 0.66, 1.00, 1.00, 1.00, 0.75]),
                            'fnr' : np.array([0.00, 0.00, 1.00, 0.50, 0.00, 0.00]),
                            'prv' : np.array([0.25, 0.25, 0.50, 0.50, 0.50, 0.00]),
                            'ppv' : np.array([0.50, 0.50, 1.00, 1.00, 1.00, 0.00]),
                            'fdr' : np.array([0.50, 0.50, 0.00, 0.00, 0.00, 1.00]),
                            'for' : np.array([0.00, 0.00, 0.50, 0.33, 0.00, 0.00]),
                            'npv' : np.array([1.00, 1.00, 0.50, 0.66, 1.00, 1.00]),
                            'plr' : np.array([3.00, 3.00, 0.00, np.inf, np.inf, 4.00]),
                            'nlr' : np.array([0.00, 0.00, 1.00, 0.50, 0.00, 0.00]),
                            'dor' : np.array([np.inf, np.inf, 0.00, np.inf, np.inf, np.inf]),
                            'fos' : np.array([0.66, 0.66, 0.00, 0.66, 1.00, 0.00]),
                            'jac' : np.array([0.49, 0.49, 0.00, 0.49, 1.00, 0.00])}),

              (None, 'micro', {'tpr' : np.array([0.50, 0.75]),
                               'fpr' : np.array([0.25, 0.12]),
                               'tnr' : np.array([0.75, 0.87]),
                               'fnr' : np.array([0.50, 0.25]),
                               'prv' : np.array([0.33, 0.33]),
                               'ppv' : np.array([0.50, 0.75]),
                               'fdr' : np.array([0.50, 0.25]),
                               'for' : np.array([0.25, 0.12]),
                               'npv' : np.array([0.75, 0.87]),
                               'plr' : np.array([3.00, 10.00]),
                               'nlr' : np.array([0.42, 0.18]),
                               'dor' : np.array([6.00, np.inf]),
                               'fos' : np.array([0.50, 0.75]),
                               'jac' : np.array([0.33, 0.60])}),

              (None, 'macro', {'tpr' : np.array([0.66, 0.83]),
                               'fpr' : np.array([0.22, 0.08]),
                               'tnr' : np.array([0.77, 0.91]),
                               'fnr' : np.array([0.33, 0.16]),
                               'prv' : np.array([0.33, 0.33]),
                               'ppv' : np.array([0.66, 0.66]),
                               'fdr' : np.array([0.33, 0.33]),
                               'for' : np.array([0.16, 0.11]),
                               'npv' : np.array([0.83, 0.88]),
                               'plr' : np.array([2.00, 4.00]),
                               'nlr' : np.array([0.33, 0.16]),
                               'dor' : np.array([0.00, np.inf]),
                               'fos' : np.array([0.66, 0.74]),
                               'jac' : np.array([0.50, 0.58])}),

              ('mean', None, {'tpr' : np.array([0.75, 1.00, 0.50]),
                              'fpr' : np.array([0.16, 0.16, 0.12]),
                              'tnr' : np.array([0.83, 0.83, 0.87]),
                              'fnr' : np.array([0.25, 0.00, 0.50]),
                              'prv' : np.array([0.37, 0.37, 0.25]),
                              'ppv' : np.array([0.75, 0.75, 0.50]),
                              'fdr' : np.array([0.25, 0.25, 0.50]),
                              'for' : np.array([0.16, 0.00, 0.25]),
                              'npv' : np.array([0.83, 1.00, 0.75]),
                              'plr' : np.array([3.00, 3.00, 2.00]),
                              'nlr' : np.array([0.25, 0.00, 0.50]),
                              'dor' : np.array([np.inf, np.inf, 0.00]),
                              'fos' : np.array([0.66, 0.83, 0.00]),
                              'jac' : np.array([0.50, 0.75, 0.00])}),

              ('mean', 'micro', {'tpr' : np.array([0.62]),
                                 'fpr' : np.array([0.18]),
                                 'tnr' : np.array([0.81]),
                                 'fnr' : np.array([0.37]),
                                 'prv' : np.array([0.33]),
                                 'ppv' : np.array([0.62]),
                                 'fdr' : np.array([0.37]),
                                 'for' : np.array([0.18]),
                                 'npv' : np.array([0.81]),
                                 'plr' : np.array([6.50]),
                                 'nlr' : np.array([0.30]),
                                 'dor' : np.array([6.00]),
                                 'fos' : np.array([0.62]),
                                 'jac' : np.array([0.46])}),

              ('mean', 'macro', {'tpr' : np.array([0.75]),
                                 'fpr' : np.array([0.15]),
                                 'tnr' : np.array([0.84]),
                                 'fnr' : np.array([0.25]),
                                 'prv' : np.array([0.33]),
                                 'ppv' : np.array([0.66]),
                                 'fdr' : np.array([0.33]),
                                 'for' : np.array([0.13]),
                                 'npv' : np.array([0.86]),
                                 'plr' : np.array([3.00]),
                                 'nlr' : np.array([0.25]),
                                 'dor' : np.array([0.00]),
                                 'fos' : np.array([0.70]),
                                 'jac' : np.array([0.54])})]

    @pytest.mark.parametrize('batch_agg, multi_agg, exp_dict', params)
    def test_contents(self, batch_agg, multi_agg, exp_dict):

        metric = SegmentationMetricsByPixels(targets, labels, 'labels', num_classes)
        for alias, exp in exp_dict.items():
            metric_names = metrics_dict[alias]
            for metric_name in metric_names:
                res = metric.evaluate(metrics=metric_name, agg=batch_agg, multiclass=multi_agg)
                res = res.reshape(-1) if isinstance(res, np.ndarray) else [res]

                assert np.allclose(res, exp, atol=1e-02, rtol=0), 'failed on metric {}'.format(metric_name)

    # Individual test params for accuracy — batch-only aggregation param and corresponding expected metrics contents.
    params_accuracy = [(None, np.array([0.50, 0.75])),
                       ('mean', np.array([0.62]))]

    @pytest.mark.parametrize('batch_agg, exp', params_accuracy)
    def test_contents_accuracy(self, batch_agg, exp):

        metric = SegmentationMetricsByPixels(targets, labels, 'labels', num_classes)
        res = metric.evaluate(metrics='accuracy', agg=batch_agg)
        res = res.reshape(-1) if isinstance(res, np.ndarray) else [res]

        assert np.allclose(res, exp, atol=1e-02, rtol=0), 'failed on metric {}'.format('accuracy')