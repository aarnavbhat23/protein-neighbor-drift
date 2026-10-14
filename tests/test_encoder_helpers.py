import unittest
import importlib.util
from encode_esm import composition

class CompositionTests(unittest.TestCase):
    def test_frequency_not_raw_counts(self):
        self.assertEqual(composition('AAAA'),composition('AA'))
        self.assertAlmostEqual(sum(composition('ACDE')),1)
    def test_noncanonical_is_rejected(self):
        with self.assertRaises(ValueError): composition('AX')

    @unittest.skipUnless(importlib.util.find_spec('torch'), 'Optional torch dependencies not installed')
    def test_pooling_excludes_padding_and_special_tokens(self):
        import torch
        from encode_esm import mean_residues
        hidden=torch.tensor([[[100.],[2.],[4.],[100.],[999.]]])
        attention=torch.tensor([[1,1,1,1,0]])
        special=torch.tensor([[1,0,0,1,0]])
        self.assertEqual(mean_residues(hidden,attention,special).item(),3)
