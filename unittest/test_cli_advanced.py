#!/usr/bin/env python3
"""Tests for advanced CLI functionality of SplinalTap."""

import unittest
import sys
import os
import json
import tempfile
import subprocess
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch
import argparse

# Import CLI module
from splinaltap.cli import (
    main, parse_method_parameters, sanitize_for_ast, 
    scene_cmd, generate_scene_cmd, backend_cmd
)

class TestCLIAdvanced(unittest.TestCase):
    """Test advanced CLI functionality."""
    
    def setUp(self):
        """Set up test case."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        self.temp_dir.cleanup()
    
    def test_parse_method_parameters(self):
        """Test parsing of method parameters."""
        # Test simple method without parameters
        method_name, params = parse_method_parameters("cubic")
        self.assertEqual(method_name, "cubic")
        self.assertIsNone(params)
        
        # Test method with key=value parameters
        method_name, params = parse_method_parameters("hermite{deriv=2.5}")
        self.assertEqual(method_name, "hermite")
        self.assertIsNotNone(params)
        self.assertIn("deriv", params)
        self.assertEqual(params["deriv"], "2.5")
        
        # Test method with complex control point parameters
        method_name, params = parse_method_parameters("bezier{cp=0.1,2.0,0.3,-4.0}")
        self.assertEqual(method_name, "bezier")
        self.assertIsNotNone(params)
        self.assertIn("cp", params)
        self.assertEqual(params["cp"], "0.1,2.0,0.3,-4.0")
    
    def test_sanitize_for_ast(self):
        """Test sanitization of expressions for AST parsing."""
        # Test power operator conversion
        sanitized = sanitize_for_ast("2^3")
        self.assertEqual(sanitized, "2**3")
        
        # Test with variables
        sanitized = sanitize_for_ast("x^2 + y^3")
        self.assertEqual(sanitized, "x**2 + y**3")
        
        # Test with @ symbol (should be preserved)
        sanitized = sanitize_for_ast("sin(@ * pi)")
        self.assertEqual(sanitized, "sin(@ * pi)")
    
    def test_content_types(self):
        """Test different output content types."""
        # Create base command
        base_cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--keyframes', '0:0', '1:10',
            '--samples', '0', '0.5', '1'
        ]
        
        # Test JSON output
        json_output = os.path.join(self.temp_dir.name, 'output.json')
        json_cmd = base_cmd + ['--output-file', json_output, '--content-type', 'json']
        
        result = subprocess.run(json_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(json_output))
        
        # Verify JSON structure
        with open(json_output, 'r') as f:
            data = json.load(f)
        self.assertIn('samples', data)
        self.assertIn('results', data)
        
        # Test CSV output
        csv_output = os.path.join(self.temp_dir.name, 'output.csv')
        csv_cmd = base_cmd + ['--output-file', csv_output, '--content-type', 'csv']
        
        result = subprocess.run(csv_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(csv_output))
        
        # Verify CSV structure (just check it exists and has content)
        with open(csv_output, 'r') as f:
            content = f.read()
        self.assertGreater(len(content), 0)
        
        # Test TEXT output
        text_output = os.path.join(self.temp_dir.name, 'output.txt')
        text_cmd = base_cmd + ['--output-file', text_output, '--content-type', 'text']
        
        result = subprocess.run(text_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(text_output))
        
        # Verify TEXT structure (just check it exists and has content)
        with open(text_output, 'r') as f:
            content = f.read()
        self.assertGreater(len(content), 0)
    
    def test_scene_generation_command(self):
        """Test the generate-scene command."""
        # Create a temporary output file
        output_file = os.path.join(self.temp_dir.name, 'scene.json')
        
        # Run the command
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--generate-scene', output_file,
            '--keyframes', '0:0', '0.5:5', '1:10',
            '--dimensions', '3'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify that the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Load the file and verify structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Verify basic scene structure
        self.assertIn('name', data)
        self.assertIn('metadata', data)
        self.assertIn('splines', data)
        
        # Since we provided keyframes, they should be used
        # Find a spline with our keyframes
        found_keyframes = False
        
        for spline in data['splines']:
            if 'channels' in spline:
                for channel in spline['channels']:
                    if 'keyframes' in channel and len(channel['keyframes']) == 3:
                        kf_positions = [kf[0] for kf in channel['keyframes']]
                        if 0.0 in kf_positions and 0.5 in kf_positions and 1.0 in kf_positions:
                            found_keyframes = True
                            break
        
        self.assertTrue(found_keyframes, "Generated scene doesn't contain the expected keyframes")
    
    def test_scene_info_command(self):
        """Test the scene info command."""
        # First, create a scene file
        scene_file = os.path.join(self.temp_dir.name, 'scene.json')
        
        # Generate a scene
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--generate-scene', scene_file,
            '--keyframes', '0:0', '1:10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Now test the scene info command
        info_cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--scene', f'info {scene_file}'
        ]
        
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the output contains basic scene information
        self.assertIn('Solver:', result.stdout)
        self.assertIn('Splines:', result.stdout)
    
    def test_scene_ls_command(self):
        """Test the scene ls command."""
        # First, create a scene file
        scene_file = os.path.join(self.temp_dir.name, 'scene.json')
        
        # Generate a scene with multiple splines
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--generate-scene', scene_file,
            '--keyframes', '0:0', '1:10',
            '--dimensions', '3'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Now test the scene ls command
        ls_cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--scene', f'ls {scene_file}'
        ]
        
        result = subprocess.run(ls_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the output contains spline names
        self.assertIn('Solver:', result.stdout)
        # Default generated scene should have a position spline
        self.assertIn('position', result.stdout)
    
    def test_scene_extract_command(self):
        """Test the scene extract command."""
        # First, create a scene file
        scene_file = os.path.join(self.temp_dir.name, 'scene.json')
        
        # Generate a scene with multiple dimensions
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--generate-scene', scene_file,
            '--dimensions', '3'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Extract file path
        extract_file = os.path.join(self.temp_dir.name, 'extracted.json')
        
        # Test extracting a whole spline
        extract_cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--scene', f'extract {scene_file} {extract_file} position'
        ]
        
        result = subprocess.run(extract_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the extract file was created
        self.assertTrue(os.path.exists(extract_file))
        
        # Test extracting a specific channel
        channel_extract_file = os.path.join(self.temp_dir.name, 'channel_extract.json')
        
        channel_extract_cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--scene', f'extract {scene_file} {channel_extract_file} position x'
        ]
        
        result = subprocess.run(channel_extract_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the channel extract file was created
        self.assertTrue(os.path.exists(channel_extract_file))
    
    def test_expression_keyframes(self):
        """Test keyframes with expressions."""
        # Create a temporary output file
        output_file = os.path.join(self.temp_dir.name, 'output.json')
        
        # Run command with expression keyframes
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--keyframes', '0:0', '0.5:sin(@ * pi)', '1:0',
            '--samples', '0', '0.25', '0.5', '0.75', '1',
            '--output-file', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the output file
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check the values
        values = data['results']['default.value']
        
        # Check that the expression is evaluated correctly
        # At @ = 0.5, sin(0.5 * π) = 1.0
        self.assertAlmostEqual(values[2], 1.0, places=5)
        
        # Midpoints should interpolate toward and away from the peak
        self.assertGreater(values[1], 0.0)  # 0.25 should be between 0 and 1
        self.assertLess(values[1], 1.0)
        
        self.assertGreater(values[3], 0.0)  # 0.75 should be between 0 and 1
        self.assertLess(values[3], 1.0)
    
    def test_custom_sample_range(self):
        """Test using custom sample range."""
        # Create a temporary output file
        output_file = os.path.join(self.temp_dir.name, 'output.json')
        
        # Run command with custom range
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--keyframes', '0:0', '1:10',
            '--samples', '5',  # 5 samples
            '--range', '2,3',  # From 2 to 3
            '--output-file', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the output file
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check that sample points are in the specified range
        samples = data['samples']
        self.assertEqual(len(samples), 5)
        
        # Check that samples span the specified range
        self.assertAlmostEqual(min(samples), 2.0, places=5)
        self.assertAlmostEqual(max(samples), 3.0, places=5)
    
    def test_use_indices_mode(self):
        """Test using absolute indices instead of normalized positions."""
        # Create a temporary output file
        output_file = os.path.join(self.temp_dir.name, 'output.json')
        
        # Run command with use_indices mode
        cmd = [
            sys.executable, '-m', 'splinaltap.cli',
            '--keyframes', '0:0', '5:5', '10:10',
            '--use-indices',
            '--samples', '0', '5', '10',
            '--output-file', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Verify the output file
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check the values - indices are normalized to 0-1 range internally
        values = data['results']['default.value']
        self.assertEqual(len(values), 3)
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[1], 5.0)
        self.assertEqual(values[2], 10.0)

if __name__ == "__main__":
    unittest.main()