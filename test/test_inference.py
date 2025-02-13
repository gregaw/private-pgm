import unittest
from mbi.domain import Domain
from mbi.inference import FactoredInference
from mbi.graphical_model import CliqueVector
import numpy as np


def _calculate_loss(engine):
    return engine._marginal_loss(engine.model.marginals)[0]


class TestInference(unittest.TestCase):

    def setUp(self):
        attrs = ['a', 'b', 'c', 'd', 'e']
        shape = [2, 3, 4, 5, 6]
        self.domain = Domain(attrs, shape)

        # x = np.random.rand(*shape)

        self.measurements = []
        for i in range(4):
            I = np.eye(shape[i])
            y = np.random.rand(shape[i])
            y /= y.sum()
            self.measurements.append((I, y, 1.0, attrs[i]))

        self.engine = FactoredInference(self.domain, backend='numpy', log=True, iters=100, warm_start=True)
        self.early_stop_loss = .02
        self.engine_early_stop = FactoredInference(self.domain, backend=self.engine.backend, log=self.engine.log,
                                                   iters=self.engine.iters, warm_start=self.engine.warm_start,
                                                   early_stop_loss=self.early_stop_loss)

    def test_estimate(self):
        self.engine.estimate(self.measurements, 1.0)
        self.assertEqual(self.engine.model.total, 1.0)

    def test_mirror_descent(self):
        loss = self.engine.mirror_descent(self.measurements, 1.0)
        self.assertEqual(self.engine.model.total, 1.0)
        self.assertTrue(loss <= 1e-4)

    def test_dual_averaging(self):
        loss = self.engine.dual_averaging(self.measurements, 1.0)
        self.assertEqual(self.engine.model.total, 1.0)
        # self.assertTrue(loss <= 1e-5)

    def test_interior_gradient(self):
        loss = self.engine.interior_gradient(self.measurements, 1.0)
        self.assertEqual(self.engine.model.total, 1.0)
        # self.assertTrue(loss <= 1e-5)

    def test_warm_start(self):
        self.engine.estimate(self.measurements, 1.0)
        new = (np.eye(2 * 3), np.random.rand(6), 1.0, ('a', 'b'))
        self.engine.estimate(self.measurements + [new], 1.0)

    def test_lipschitz(self):
        self.engine._setup(self.measurements, None)
        lip = self.engine._lipschitz(self.measurements)

        def rand():
            ans = {}
            for cl in self.engine.model.cliques:
                ans[cl] = self.engine.Factor.random(self.engine.domain.project(cl))
            return CliqueVector(ans)

        for _ in range(100):
            x = rand()
            y = rand()
            _, gx = self.engine._marginal_loss(x)
            _, gy = self.engine._marginal_loss(y)
            A = (gx - gy).dot(gx - gy)
            B = (x - y).dot(x - y)
            ratio = np.sqrt(A / B)
            self.assertTrue(ratio <= lip)

    # would love to use `parameterized` tests here, but don't want to add any new dependencies
    def test_mirror_descent_early_stop(self):
        loss = self.engine.mirror_descent(self.measurements, 1.0)
        loss_early_stop = self.engine_early_stop.mirror_descent(self.measurements, 1.0)

        self.assertLess(loss, loss_early_stop)

    def test_dual_averaging_early_stop(self):
        self.engine.dual_averaging(self.measurements, 1.0)
        self.engine_early_stop.dual_averaging(self.measurements, 1.0)

        self.assertLess(_calculate_loss(self.engine), _calculate_loss(self.engine_early_stop))

    def test_interior_gradient_early_stop(self):
        self.engine.interior_gradient(self.measurements, 1.0)
        self.engine_early_stop.interior_gradient(self.measurements, 1.0)

        self.assertLess(_calculate_loss(self.engine), _calculate_loss(self.engine_early_stop))


if __name__ == '__main__':
    unittest.main()
