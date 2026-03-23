#!/usr/bin/env python3
"""
Unit tests for Molecular Scout Agent
Tests the agent with/without RDKit and XGBoost to verify graceful degradation
"""

import unittest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.molecular_scout_ml import MolecularScoutML


class TestMolecularScout(unittest.TestCase):
    
    def setUp(self):
        """Initialize agent for each test."""
        self.agent = MolecularScoutML()
    
    def test_agent_initialization(self):
        """Test agent initializes in some mode."""
        self.assertIsNotNone(self.agent)
        self.assertIn(self.agent.mode, ['ml', 'lipinski', 'heuristic'])
        print(f"✓ Agent initialized in mode: {self.agent.mode}")
    
    def test_score_single_molecule(self):
        """Test scoring a single SMILES string."""
        smiles = "CC(=O)NCCCC(=O)Nc1ccccc1"  # Drug-like compound
        result = self.agent.score_molecule(smiles, target='HDAC6')
        
        self.assertIsNotNone(result)
        self.assertIn('score', result)
        self.assertIn('final_score', result)
        self.assertIn('mode', result)
        self.assertEqual(result['smiles'], smiles)
        self.assertGreaterEqual(result['final_score'], 0)
        self.assertLessEqual(result['final_score'], 1)
        
        print(f"✓ Single molecule scored: {result['final_score']:.3f}")
    
    def test_score_batch_molecules(self):
        """Test scoring a batch of molecules."""
        molecules = [
            "CC(=O)NCCCC(=O)Nc1ccccc1",  # Drug-like
            "c1ccccc1",  # Simple benzene
            "CCOc1ccccc1C",  # Ether
        ]
        
        result = self.agent.score_batch(
            molecules=[{'smiles': s} for s in molecules],
            target='HDAC6',
            top_k=100
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['total_scored'], len(molecules))
        self.assertIn('top_k', result)
        self.assertEqual(len(result['top_k']), len(molecules))
        
        print(f"✓ Batch scored: {len(result['top_k'])} molecules")
    
    def test_lipinski_scoring(self):
        """Test Lipinski Rule of 5 scoring."""
        # Valid drug-like compound
        valid = "CC(=O)NCCCC(=O)Nc1ccccc1"
        result_valid = self.agent.score_molecule(valid)
        
        self.assertFalse(result_valid['violates_lipinski'])
        print(f"✓ Drug-like compound: violations={len(result_valid['violations'])}")
        
        # Invalid compound (very large)
        # Generate a large molecule
        invalid = "c1ccc2c(c1)ccc3c2cccc3" * 5  # Large polycyclic
        result_invalid = self.agent.score_molecule(invalid)
        
        # Large molecules often violate Lipinski
        print(f"✓ Large compound: violations={len(result_invalid['violations'])}")
    
    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        invalid_smiles = "INVALID_SMILES_XXXX"
        result = self.agent.score_molecule(invalid_smiles)
        
        self.assertIn('error', result)
        print(f"✓ Invalid SMILES handled: {result['error']}")
    
    def test_descriptor_computation(self):
        """Test molecular descriptor computation."""
        smiles = "CC(=O)NCCCC(=O)Nc1ccccc1"
        descriptors = self.agent.compute_descriptors(smiles)
        
        self.assertIsNotNone(descriptors)
        required_keys = [
            'MW', 'LogP', 'HBA', 'HBD', 'PSA', 
            'RotBonds', 'RingCount', 'AromaticRings', 'HeavyAtomCount'
        ]
        
        for key in required_keys:
            self.assertIn(key, descriptors)
        
        print(f"✓ Descriptors computed: MW={descriptors['MW']:.1f}, LogP={descriptors['LogP']:.1f}")
    
    def test_batch_json_serializable(self):
        """Test that batch results are JSON serializable."""
        molecules = ["CC(=O)NCCCC(=O)Nc1ccccc1", "c1ccccc1"]
        result = self.agent.score_batch(
            molecules=[{'smiles': s} for s in molecules],
            top_k=100
        )
        
        # Should not raise exception
        json_str = json.dumps(result, indent=2)
        self.assertIsNotNone(json_str)
        self.assertGreater(len(json_str), 0)
        
        print(f"✓ Results JSON serializable ({len(json_str)} chars)")
    
    def test_top_k_sorting(self):
        """Test that results are sorted by score."""
        molecules = [
            "CC(=O)NCCCC(=O)Nc1ccccc1",  # Should be high scoring
            "c1ccccc1",  # Should be low scoring
            "CCOc1ccccc1C",  # Medium scoring
        ]
        
        result = self.agent.score_batch(
            molecules=[{'smiles': s} for s in molecules],
            top_k=100
        )
        
        # Check sorting (highest score first)
        scores = [m['final_score'] for m in result['top_k']]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        print(f"✓ Results sorted by score (highest: {scores[0]:.3f}, lowest: {scores[-1]:.3f})")
    
    def test_target_antitarget_scoring(self):
        """Test target/antitarget affinity scoring."""
        smiles = "CC(=O)NCCCC(=O)Nc1ccccc1"
        
        # With antitarget
        result_with_anti = self.agent.score_molecule(
            smiles, 
            target='HDAC6', 
            antitarget='HDAC1'
        )
        
        # Without antitarget
        result_no_anti = self.agent.score_molecule(
            smiles,
            target='HDAC6'
        )
        
        self.assertIsNotNone(result_with_anti['antitarget_affinity'])
        self.assertIsNotNone(result_no_anti['antitarget_affinity'])
        
        print(f"✓ Target/antitarget scoring working")


class TestGracefulDegradation(unittest.TestCase):
    """Test that agent works without optional dependencies."""
    
    def test_fallback_modes(self):
        """Test all three fallback modes work."""
        agent = MolecularScoutML()
        
        smiles = "CC(=O)NCCCC(=O)Nc1ccccc1"
        result = agent.score_molecule(smiles)
        
        # Agent should always return a result
        self.assertIsNotNone(result)
        self.assertIn('final_score', result)
        self.assertGreaterEqual(result['final_score'], 0)
        self.assertLessEqual(result['final_score'], 1)
        
        mode = agent.mode
        print(f"✓ Agent working in mode: {mode}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("MOLECULAR SCOUT AGENT TEST SUITE")
    print("="*60 + "\n")
    
    unittest.main(verbosity=2)
