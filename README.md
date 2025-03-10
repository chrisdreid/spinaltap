# splinaltap

*Keyframe interpolation and expression evaluation that goes to eleven!*

## About splinaltap

splinaltap is a Python library that provides powerful tools for working with keyframes, expressions, and spline interpolation. It allows you to define keyframes with mathematical expressions, evaluate them at any point along a timeline, and interpolate between them using various methods.

### Why the Name?

The name "splinaltap" is a playful nod to the mockumentary "This Is Spinal Tap" and its famous "these go to eleven" scene - because sometimes regular interpolation just isn't enough. But more importantly:

- **splin**: Refers to splines, the mathematical curves used for smooth interpolation
- **al**: Represents algorithms and algebraic expressions
- **tap**: Describes how you can "tap into" the curve at any point to extract values

## Key Features

- 🔢 **Safe Expression Evaluation**: Define keyframes using string expressions that are safely evaluated using Python's AST
- 🔄 **Multiple Interpolation Methods**: Choose from 9 different interpolation algorithms:
  - Nearest Neighbor
  - Linear
  - Polynomial (Lagrange)
  - Quadratic Spline
  - Cubic Spline
  - Hermite Interpolation
  - Bezier Interpolation
  - PCHIP (Piecewise Cubic Hermite Interpolating Polynomial)
  - Gaussian Process Interpolation (requires NumPy)
- 🧮 **Variable Support**: Define and use variables in your expressions for complex animations and simulations
- 🎛️ **Channel Support**: Pass in dynamic channel values that can be used in expressions
- 📊 **Visualization**: Built-in support for visualizing interpolation results
- 🔒 **Safe Execution**: No unsafe `eval()` - all expressions are parsed and evaluated securely
- 🚀 **GPU Acceleration**: Optional GPU support via CuPy or JAX for faster processing

## Installation

```bash
pip install splinaltap
```

### Optional Dependencies

For enhanced performance, you can install NumPy (CPU acceleration) or GPU acceleration libraries:

```bash
# For NumPy support (CPU acceleration)
pip install numpy

# For CUDA 11.x GPU support
pip install cupy-cuda11x

# For CUDA 12.x GPU support
pip install cupy-cuda12x

# For JAX support (GPU acceleration with autodiff)
pip install "jax[cuda]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
```

### Verifying CUDA Installation

You can verify your CUDA installation is working properly with:

```python
import splinaltap
from splinaltap.backends import BackendManager

# Check available backends
print(BackendManager.available_backends())  # Should include 'cupy' if installed correctly

# Set backend to CuPy
BackendManager.set_backend('cupy')

# Create a sample and verify it's using GPU
interpolator = splinaltap.KeyframeInterpolator(10)
interpolator.set_keyframe(0.0, 0)
interpolator.set_keyframe(10.0, 10)

# Generate samples using GPU
samples = interpolator.sample_with_gpu(0, 10, 1000)
print(f"Backend used: {BackendManager.get_backend().name}")
print(f"Supports GPU: {BackendManager.get_backend().supports_gpu}")
```

## Quick Start

```python
from splinaltap import KeyframeInterpolator
import matplotlib.pyplot as plt

# Create a KeyframeInterpolator instance with 10 indices
interpolator = KeyframeInterpolator(10)

# Add keyframes with expressions
interpolator.set_keyframe(0.0, 0)
interpolator.set_keyframe(2.5, "sin(t) + 1")  # 't' is the current time
interpolator.set_keyframe(5.7, "pow(t, 2)")
interpolator.set_keyframe(10.0, 10)

# Define a variable
interpolator.set_variable("amplitude", 2.5)
interpolator.set_keyframe(7.0, "amplitude * sin(t)")

# Evaluate at various points
t_values = [i * 0.1 for i in range(101)]
values = [interpolator.get_value(t, "cubic") for t in t_values]

# Plot the results
plt.figure(figsize=(12, 6))
plt.plot(t_values, values)
plt.title("Cubic Spline Interpolation")
plt.grid(True)
plt.show()
```

## Advanced Usage

### Using Different Interpolation Methods

```python
# Compare different interpolation methods
methods = ["linear", "cubic", "hermite", "bezier"]
plt.figure(figsize=(12, 8))

for method in methods:
    values = [interpolator.get_value(t, method) for t in t_values]
    plt.plot(t_values, values, label=method.capitalize())

plt.legend()
plt.title("Interpolation Methods Comparison")
plt.show()
```

### Using Channels

```python
# Define keyframes that use channel values
interpolator.set_keyframe(3.0, "a * sin(t) + b")

# Evaluate with different channel values
channels_1 = {"a": 1.0, "b": 0.5}
channels_2 = {"a": 2.0, "b": 0.0}

values_1 = [interpolator.get_value(t, "cubic", channels_1) for t in t_values]
values_2 = [interpolator.get_value(t, "cubic", channels_2) for t in t_values]
```

### Using Control Points (Bezier)

```python
# Set keyframe with control points for Bezier interpolation
interpolator.set_keyframe(4.0, 5.0, derivative=None, control_points=(4.2, 6.0, 4.8, 7.0))
```

### Using GPU Acceleration

```python
from splinaltap import KeyframeInterpolator
from splinaltap.backends import BackendManager

# Set backend to CuPy if available
try:
    BackendManager.set_backend('cupy')
    print("Using CuPy GPU acceleration")
except Exception:
    print("CuPy not available, using fallback backend")

# Create interpolator and keyframes
interpolator = KeyframeInterpolator(10)
interpolator.set_keyframe(0.0, 0)
interpolator.set_keyframe(10.0, 10)

# Generate 1 million samples efficiently using GPU
samples = interpolator.sample_with_gpu(0, 10, 1_000_000)
```

## Applications

- Animation systems
- Scientific data interpolation
- Audio parameter automation
- Financial data modeling
- Simulation systems
- Game development
- Procedural content generation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
