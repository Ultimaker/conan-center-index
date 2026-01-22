import os
import shutil
import textwrap
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import Environment, VirtualBuildEnv
from conan.tools.files import get, copy, save, chdir
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.0"


class ShapelyConan(ConanFile):
    name = "shapely"
    description = "Manipulation and analysis of geometric objects in the Cartesian plane"
    license = "BSD-3-Clause"
    author = "Sean Gillies and contributors"
    homepage = "https://github.com/shapely/shapely"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("geometry", "gis", "geospatial", "cartesian", "geos")
    
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    
    def requirements(self):
        # Shapely requires GEOS >= 3.5
        self.requires("geos/3.12.2")
        # Note: Shapely requires NumPy for array operations at runtime
        # NumPy should be available in the target Python environment
    
    def configure(self):
        # Ensure GEOS is built as shared library for proper linking
        self.options["geos"].shared = True
        if self.settings.os != "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        # Shapely 2.x requires Python >= 3.8
        if Version(self.version) >= "2.0" and Version(self.version) < "3.0":
            self.output.info("Shapely 2.x requires Python >= 3.8")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], 
            destination=self.source_folder, strip_root=True)

    def generate(self):
        # Set up build environment with GEOS paths
        env = Environment()
        
        # Get GEOS dependency information
        geos_dep = self.dependencies["geos"]
        geos_cpp_info = geos_dep.cpp_info
        
        # Add GEOS binary directory to PATH (for geos-config)
        for bindir in geos_cpp_info.bindirs:
            geos_bin_path = os.path.join(geos_dep.package_folder, bindir)
            env.prepend_path("PATH", geos_bin_path)
        
        # Set GEOS environment variables for shapely build
        if geos_cpp_info.includedirs:
            include_dirs = os.pathsep.join([
                os.path.join(geos_dep.package_folder, inc) 
                for inc in geos_cpp_info.includedirs
            ])
            env.define("GEOS_INCLUDE_PATH", include_dirs)
        
        if geos_cpp_info.libdirs:
            lib_dirs = os.pathsep.join([
                os.path.join(geos_dep.package_folder, lib) 
                for lib in geos_cpp_info.libdirs
            ])
            env.define("GEOS_LIBRARY_PATH", lib_dirs)
        
        # Set GEOS_CONFIG path if available
        for bindir in geos_cpp_info.bindirs:
            geos_config = os.path.join(geos_dep.package_folder, bindir, "geos-config")
            if os.path.exists(geos_config):
                env.define("GEOS_CONFIG", geos_config)
                break
            # On Windows, it might be geos-config.exe
            geos_config_exe = geos_config + ".exe"
            if os.path.exists(geos_config_exe):
                env.define("GEOS_CONFIG", geos_config_exe)
                break
        
        # Apply the environment
        env.vars(self, scope="build").save_script("conan_shapely_env")

    def build(self):
        with chdir(self, self.source_folder):
            # Create a simple setup script that builds shapely with the environment
            setup_script = textwrap.dedent("""
                import sys
                import subprocess
                import os
                
                def main():
                    # Build shapely using pip with current environment
                    # This ensures GEOS environment variables are available
                    cmd = [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", "dist"]
                    
                    print(f"Building shapely with command: {' '.join(cmd)}")
                    print(f"GEOS_CONFIG: {os.environ.get('GEOS_CONFIG', 'not set')}")
                    print(f"GEOS_INCLUDE_PATH: {os.environ.get('GEOS_INCLUDE_PATH', 'not set')}")
                    print(f"GEOS_LIBRARY_PATH: {os.environ.get('GEOS_LIBRARY_PATH', 'not set')}")
                    print(f"PATH: {os.environ.get('PATH', 'not set')}")
                    
                    result = subprocess.run(cmd, check=True)
                    return result.returncode
                
                if __name__ == "__main__":
                    sys.exit(main())
            """)
            
            save(self, "build_shapely.py", setup_script)
            
            # Create dist directory
            os.makedirs("dist", exist_ok=True)
            
            # Run the build script with the environment
            self.run(f"python build_shapely.py", cwd=self.source_folder)

    def package(self):
        # Copy the built wheel to the package folder
        copy(self, "*.whl", src=os.path.join(self.source_folder, "dist"), 
             dst=os.path.join(self.package_folder, "dist"))
        
        # Copy license
        copy(self, "LICENSE*", src=self.source_folder, 
             dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        # Add the wheel to the Python path information
        wheel_dir = os.path.join(self.package_folder, "dist")
        if os.path.exists(wheel_dir):
            wheels = [f for f in os.listdir(wheel_dir) if f.endswith('.whl')]
            if wheels:
                self.cpp_info.bindirs.append("dist")
                # Set environment variable to indicate the wheel location
                self.runenv_info.define("SHAPELY_WHEEL", os.path.join(wheel_dir, wheels[0]))