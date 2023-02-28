from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout

import os

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeToolchain", "CMakeDeps"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self, src_folder=".")

    def build(self):
        cmake = CMake(self)
        cmake.configure(variables={"MPDECIMAL_CXX":  self.dependencies["mpdecimal"].options.cxx, "BUILD_SHARED": str(self.dependencies["mpdecimal"].options.shared).upper()})
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package")
            self.run(f"{bin_path} 13 100", env="conanrun")
            if self.dependencies["mpdecimal"].options.cxx:
                self.run(f"{bin_path} 13 100", env="conanrun")
