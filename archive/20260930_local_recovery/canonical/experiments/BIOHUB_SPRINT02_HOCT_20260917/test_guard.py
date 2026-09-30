import copy
import unittest
from hoct_guard import apply_guard, digest


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.nodes = {i: dict(node_id=i, t=i // 3, z=1.25, y=2.5, x=3.75) for i in range(9)}
        self.edges = [dict(source_id=u, target_id=v) for u, v in [(0, 3), (0, 4), (1, 5), (3, 6), (4, 7)]]
        self.ev = dict(video='a', input_hash=digest(['a', list(self.nodes.items()), self.edges]),
                       complete=True, covered=[[0, 3], [0, 4], [1, 5], [3, 6]], selected=[[3, 6]])

    def test_protection_coverage_and_independence(self):
        original = copy.deepcopy([self.nodes, self.edges])
        n, e, r, d = apply_guard('a', self.nodes, self.edges, self.ev)
        self.assertEqual(d, [(1, 5)])
        self.assertEqual(r['protected'], 2)
        self.assertEqual(n, self.nodes)
        self.assertEqual([self.nodes, self.edges], original)
        n[0]['x'] = 99
        self.assertNotEqual(n, self.nodes)
        self.assertIn(dict(source_id=4, target_id=7), e)

    def test_fallbacks(self):
        for reason in ['MAPPING_MISSING', 'SPHERE_LOSS', 'INFERENCE_ERROR', 'TIMEOUT', 'BUDGET', 'PARTIAL_SOLVE']:
            ev = dict(self.ev, complete=False, reason=reason)
            n, e, r, d = apply_guard('a', self.nodes, self.edges, ev)
            self.assertEqual((n, e, d), (self.nodes, self.edges, []))
            self.assertEqual(r['status'], reason)

    def test_wrong_video_input_and_disabled(self):
        for ev in [None, dict(self.ev, video='b'), dict(self.ev, input_hash='wrong')]:
            self.assertEqual(apply_guard('a', self.nodes, self.edges, ev)[1], self.edges)
        self.assertEqual(apply_guard('a', self.nodes, self.edges, self.ev, enabled=False)[1], self.edges)

    def test_anomalous_three_children_protected(self):
        edges = self.edges + [dict(source_id=0, target_id=5)]
        ev = dict(self.ev, input_hash=digest(['a', list(self.nodes.items()), edges]), covered=[[0,3],[0,4],[0,5]])
        _, e, r, d = apply_guard('a', self.nodes, edges, ev)
        self.assertEqual(e, edges)
        self.assertEqual(r['anomalous_parents'], 1)
        self.assertEqual(d, [])


if __name__ == '__main__':
    unittest.main()
