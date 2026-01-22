from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualRunEnv"
    python_requires = "tested_reference_str"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        # Test that shapely can be imported and basic functionality works
        test_script = '''
import sys
import os

# Check if shapely wheel is available
shapely_wheel = os.environ.get('SHAPELY_WHEEL')
if shapely_wheel and os.path.exists(shapely_wheel):
    # Install the wheel temporarily for testing
    import subprocess
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Install shapely wheel to temporary directory
        cmd = [sys.executable, "-m", "pip", "install", "--target", temp_dir, shapely_wheel]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to install shapely wheel: {result.stderr}")
            sys.exit(1)
        
        # Add to Python path
        sys.path.insert(0, temp_dir)
        
        try:
            # Test basic shapely functionality
            from shapely.geometry import Point, Polygon
            from shapely.ops import unary_union
            
            # Create a simple point
            point = Point(0, 0)
            print(f"Created point: {point}")
            
            # Create a simple polygon
            polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
            print(f"Created polygon: {polygon}")
            print(f"Polygon area: {polygon.area}")
            
            # Test buffer operation (uses GEOS internally)
            buffered = point.buffer(1.0)
            print(f"Buffered point area: {buffered.area:.6f}")
            
            # Test intersection (uses GEOS internally)
            intersection = polygon.intersection(buffered)
            print(f"Intersection area: {intersection.area:.6f}")
            
            print("Shapely test passed!")
            
        except ImportError as e:
            print(f"Failed to import shapely: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error during shapely test: {e}")
            sys.exit(1)
else:
    print("SHAPELY_WHEEL environment variable not set or wheel not found")
    sys.exit(1)
'''
        
        self.run(f'python -c "{test_script}"')