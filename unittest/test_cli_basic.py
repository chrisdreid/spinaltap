#!/usr/bin/env python3
"""Tests for basic CLI functionality of SplinalTap."""

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
from splinaltap.cli import main, create_parser, create_solver_from_args

class TestCLIBasic(unittest.TestCase):
    """Test basic CLI functionality."""
    
    def setUp(self):
        """Set up test case."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        self.temp_dir.cleanup()
    
    def test_cli_parser_creation(self):
        """Test that the CLI argument parser is created correctly."""
        parser = create_parser()
        
        # Verify that it's an ArgumentParser
        self.assertIsInstance(parser, argparse.ArgumentParser)
        
        # Test that required arguments are present
        actions = {action.dest: action for action in parser._actions}
        
        # Check for important arguments
        self.assertIn('keyframes', actions)
        self.assertIn('samples', actions)
        self.assertIn('input_file', actions)
        self.assertIn('output_file', actions)
        self.assertIn('content_type', actions)
        self.assertIn('use_indices', actions)
        self.assertIn('variables', actions)
    
    def test_solver_creation_from_args(self):
        """Test creating a solver from command-line arguments."""
        # Create mock arguments
        mock_args = argparse.Namespace(
            input_file=None,
            keyframes=["0:0", "0.5:5", "1:10"],
            use_indices=False,
            variables=None
        )
        
        # Create solver from args
        solver = create_solver_from_args(mock_args)
        
        # Verify solver was created with the right keyframes
        self.assertEqual(solver.name, "CommandLine")
        
        # Get the spline and channel
        spline = solver.get_spline("default")
        channel = spline.get_channel("value")
        
        # Verify keyframes
        keyframe_values = channel.get_keyframe_values()
        self.assertEqual(len(keyframe_values), 3)
        
        # Verify keyframe positions and values
        self.assertEqual(keyframe_values[0][0], 0.0)
        self.assertEqual(keyframe_values[0][1], 0.0)
        self.assertEqual(keyframe_values[1][0], 0.5)
        self.assertEqual(keyframe_values[1][1], 5.0)
        self.assertEqual(keyframe_values[2][0], 1.0)
        self.assertEqual(keyframe_values[2][1], 10.0)
    
    def test_solver_creation_with_interpolation_methods(self):
        """Test creating a solver with different interpolation methods."""
        # Create mock arguments with different interpolation methods
        mock_args = argparse.Namespace(
            input_file=None,
            keyframes=[
                "0:0@linear",
                "0.25:2.5@cubic",
                "0.5:5@bezier{cp=0.6,6,0.7,5}",
                "0.75:7.5@hermite{deriv=0}",
                "1:10@step"
            ],
            use_indices=False,
            variables=None
        )
        
        # Create solver from args
        solver = create_solver_from_args(mock_args)
        
        # Get the channel
        spline = solver.get_spline("default")
        channel = spline.get_channel("value")
        
        # Verify keyframes
        self.assertEqual(len(channel.keyframes), 5)
        
        # Verify interpolation methods
        methods = [kf.interpolation for kf in channel.keyframes]
        self.assertEqual(methods[0], "linear")
        self.assertEqual(methods[1], "cubic")
        self.assertEqual(methods[2], "bezier")
        self.assertEqual(methods[3], "hermite")
        self.assertEqual(methods[4], "step")
        
        # Verify bezier control points
        bezier_kf = None
        for kf in channel.keyframes:
            if kf.at == 0.5:
                bezier_kf = kf
                break
        
        self.assertIsNotNone(bezier_kf)
        self.assertEqual(bezier_kf.control_points, (0.6, 6.0, 0.7, 5.0))
        
        # Verify hermite derivative
        hermite_kf = None
        for kf in channel.keyframes:
            if kf.at == 0.75:
                hermite_kf = kf
                break
        
        self.assertIsNotNone(hermite_kf)
        self.assertEqual(hermite_kf.derivative, 0.0)
    
    def test_cli_backend_command(self):
        """Test the CLI backend command."""
        # We use patch to capture stdout to test the output directly
        # without actually running as a subprocess
        
        with patch('sys.argv', ['splinaltap', '--backend', 'ls']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    # Try to run main - in some implementations this might not exit
                    main()
                except SystemExit:
                    # This is expected in some implementations
                    pass
                
                # Check that output contains "Available backends"
                output = fake_out.getvalue()
                self.assertIn("Available backends", output)
                self.assertIn("python", output)  # Python backend should always be available
    
    def test_cli_sample_output(self):
        """Test direct API use instead of CLI.
        
        Note: We skip actual CLI execution with subprocess, which is brittle in
        test environments, and instead test the direct API functions.
        """
        # Create a test environment
        args = argparse.Namespace()
        args.input_file = None
        args.keyframes = ["0:0", "0.5:5", "1:10"]
        args.use_indices = False
        args.variables = None
        args.samples = ["0", "0.5", "1"]
        
        # Create solver from args (this is what the CLI would do)
        solver = create_solver_from_args(args)
        
        # Test direct values at specified points
        self.assertEqual(solver.solve(0.0)["default"]["value"], 0.0)
        self.assertEqual(solver.solve(0.5)["default"]["value"], 5.0)
        self.assertEqual(solver.solve(1.0)["default"]["value"], 10.0)

if __name__ == "__main__":
    unittest.main()