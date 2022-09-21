import os

from conan.tools.build import cross_building
from conans import ConanFile, CMake


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package_multi"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not cross_building(self):
            bin_path = os.path.join("bin", "cminpack_test_double")
            self.run(bin_path, run_environment=True)
            bin_path = os.path.join("bin", "cminpack_test_float")
            self.run(bin_path, run_environment=True)
