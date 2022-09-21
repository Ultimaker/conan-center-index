from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeToolchain", "CMakeDeps"

    def layout(self):
        cmake_layout(self, src_folder=".")


    def build(self):
        cmake = CMake(self)
        cmake.configure(variables={"MPDECIMAL_CXX": self.options["mpdecimal"].cxx})
        cmake.build()

    def test(self):
        if can_run(self):
            self.run("{} 13 100".format(self.build_path.joinpath("test_package")), run_environment=True)
            if self.options["mpdecimal"].cxx:
                self.run("{} 13 100".format(self.build_path.joinpath("test_package_cpp")), run_environment=True)
