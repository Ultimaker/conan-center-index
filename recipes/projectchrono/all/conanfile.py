from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import check_min_vs, is_msvc_static_runtime, is_msvc
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rm, rmdir, replace_in_file
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
import os


required_conan_version = ">=1.53.0"

#
# INFO: Please, remove all comments before pushing your PR!
#


class PackageConan(ConanFile):
    name = "projectchrono"
    description = "High-performance C++ library for multiphysics and multibody dynamics simulations"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/projectchrono/chrono"
    topics = ("robotics", "simulation", "modeling", "physics-engine", "physics-simulation", "multibody-dynamics", "vehicle-dynamics", "flexible-body", "fluid-solid-interaction", "granular-dynamics")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
        "with_tbb": [True, False],
        "with_hdf5": [True, False],
        "enable_benchmarking": [True, False],
        "enable_demos": [True, False],
        "enable_module_cascade": [True, False],
        "enable_module_cosimulation": [True, False],
        "enable_module_distributed": [True, False],
        #        "enable_module_irrlicht": [True, False],  FIXME: Irrlicht is not yet supported no Conan package in CCI
        "enable_module_matlab": [True, False],
        "enable_module_mkl": [True, False],
        # "enable_module_mumps": [True, False],  FIXME: mumps is not yet supported no Conan package in CCI
        "enable_module_parallel": [True, False],
        "enable_module_opengl": [True, False],
        "enable_module_ogre": [True, False],
        "enable_module_postprocess": [True, False],
        "enable_module_python": [True, False],
        "enable_module_vehicle": [True, False],
        "enable_module_fsi": [True, False],
        "enable_module_granular": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": False,
        "with_tbb": True,
        "with_hdf5": False,
        "enable_benchmarking": False,
        "enable_demos": False,
        "enable_module_cascade": False,
        "enable_module_cosimulation": False,
        "enable_module_distributed": False,
        #        "enable_module_irrlicht": False,  FIXME: Irrlicht is not yet supported no Conan package in CCI
        "enable_module_matlab": False,
        "enable_module_mkl": False,
        # "enable_module_mumps": False,  FIXME: mumps is not yet supported no Conan package in CCI
        "enable_module_parallel": False,
        "enable_module_opengl": False,
        "enable_module_ogre": False,
        "enable_module_postprocess": False,
        "enable_module_python": False,
        "enable_module_vehicle": False,
        "enable_module_fsi": False,
        "enable_module_granular": False,
    }

    @property
    def _min_cppstd(self):
        return 14

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "6",
            "clang": "6",
            "apple-clang": "10",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        # FIXME: CUDA support for FSI https://cpplang.slack.com/archives/C41CWV9HA/p1689534061581899
        if "cuda" not in self.conf.get("tools.build:compiler_executables", default=[], check_type=list):
            del self.options.enable_module_fsi

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
            if self.options.enable_module_parallel:
                if self.options.with_openmp:  # OpenMP takes precedence over TBB
                    self.options["thrust"].device_system = "omp"
                elif self.options.with_tbb:
                    self.options["thrust"].device_system = "tbb"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/1.2.13")
        self.requires("openmpi/4.1.0")
        self.requires("eigen/3.4.0")
        if self.options.with_openmp:
            self.requires("llvm-openmp/12.0.1")
        if self.options.with_tbb:
            self.requires("onetbb/2021.9.0")
        if self.options.with_hdf5:
            self.requires("hdf5/1.14.1")
        if self.options.enable_module_opengl:
            self.requires("opengl/system")
            self.requires("glm/0.9.9.8")
            self.requires("glew/2.2.0")
            self.requires("glfw/3.3.8")
        if self.options.enable_module_parallel:
            self.requires("thrust/1.17.2")
            self.requires("blaze/3.8")
        if self.options.enable_module_python:
            self.requires("swig/4.1.0")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        check_min_vs(self, 190)
        if not is_msvc(self):
            minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
            if minimum_version and Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
                )
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} can not be built as shared on Visual Studio and msvc.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root = True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["EIGEN3_INCLUDE_DIR"] = self.deps_cpp_info["eigen"].include_paths[0]
        tc.variables["BUILD_DEMOS"] = self.options.enable_demos
        tc.variables["BUILD_BENCHMARKING"] = self.options.enable_benchmarking
        tc.variables["ENABLE_OPENMP"] = self.options.with_openmp
        tc.variables["ENABLE_TBB"] = self.options.with_tbb
        tc.variables["ENABLE_HDF5"] = self.options.with_hdf5
        tc.variables["BUILD_TESTING"] = not self.conf.get("tools.build:skip_test", default=True, check_type=bool)
        tc.variables["ENABLE_MODULE_CASCADE"] = self.options.enable_module_cascade
        tc.variables["ENABLE_MODULE_COSIMULATION"] = self.options.enable_module_cosimulation
        tc.variables["ENABLE_MODULE_DISTRIBUTED"] = self.options.enable_module_distributed
        tc.variables["ENABLE_MODULE_IRRLICHT"] = False  # FIXME: Irrlicht is not yet supported no Conan package in CCI
        tc.variables["ENABLE_MODULE_MATLAB"] = self.options.enable_module_matlab
        tc.variables["ENABLE_MODULE_MKL"] = self.options.enable_module_mkl
        tc.variables["ENABLE_MODULE_MUMPS"] = False  # FIXME: mumps is not yet supported no Conan package in CCI
        tc.variables["ENABLE_MODULE_PARALLEL"] = self.options.enable_module_parallel
        if self.options.enable_module_parallel:
            tc.variables["THRUST_INCLUDE_DIR"] = self.deps_cpp_info["thrust"].include_paths[0]
        if self.options.enable_module_opengl:
            tc.variables["GLM_INCLUDE_DIR"] = self.deps_cpp_info["glm"].include_paths[0]
            tc.variables["GLEW_INCLUDE_DIR"] = self.deps_cpp_info["glew"].include_paths[0]
            tc.variables["GLFW_INCLUDE_DIR"] = self.deps_cpp_info["glfw"].include_paths[0]
        tc.variables["ENABLE_MODULE_OPENGL"] = self.options.enable_module_opengl
        tc.variables["ENABLE_MODULE_OGRE"] = self.options.enable_module_ogre
        tc.variables["ENABLE_MODULE_POSTPROCESS"] = self.options.enable_module_postprocess
        tc.variables["ENABLE_MODULE_PYTHON"] = self.options.enable_module_python
        tc.variables["ENABLE_MODULE_VEHICLE"] = self.options.enable_module_vehicle
        tc.variables["ENABLE_MODULE_FSI"] = self.options.get_safe("enable_module_fsi", default=False)
        if self.options.get_safe("enable_module_fsi", default=False):
            tc.variables["USE_FSI_DOUBLE"] = True
        tc.variables["ENABLE_MODULE_GRANULAR"] = self.options.enable_module_granular

        if is_msvc(self):
            tc.variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)
        tc.generate()

        tc = CMakeDeps(self)
        tc.set_property("eigen", "cmake_find_mode", "module")
        tc.set_property("openmpi", "cmake_find_mode", "both")
        tc.set_property("openmpi", "cmake_file_name", "MPI")
        tc.set_property("llvm-openmp", "cmake_find_mode", "both")
        tc.set_property("onetbb", "cmake_find_mode", "module")
        tc.set_property("thrust", "cmake_find_mode", "module")
        tc.set_property("thrust", "cmake_file_name", "Thrust")
        tc.set_property("blaze", "cmake_find_mode", "module")
        tc.set_property("opengl", "cmake_find_mode", "module")
        tc.set_property("glm", "cmake_find_mode", "module")
        tc.set_property("glm", "cmake_file_name", "GLM")
        tc.set_property("glew", "cmake_find_mode", "module")
        tc.set_property("glew", "cmake_file_name", "GLEW")
        tc.set_property("glfw", "cmake_find_mode", "module")
        tc.set_property("glfw", "cmake_file_name", "GLFW")
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        rm(self, "whateer.*", os.path.join(self.source_folder, "lib"))

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern = "LICENSE", dst = os.path.join(self.package_folder, "licenses"), src = self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

        # Copy resources to res package
        copy(self, pattern = "*", dst = os.path.join(self.package_folder, "res"), src = os.path.join(self.source_folder, "data"))

    def package_info(self):
        self.cpp_info.libs = ["ChronoEngine", "ChronoModels_robot"]
        if self.options.enable_module_opengl:
            self.cpp_info.libs.append("ChronoEngine_opengl")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")

        # # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "PROJECTCHRONO"
        self.cpp_info.filenames["cmake_find_package_multi"] = "projectchrono"
        self.cpp_info.names["cmake_find_package"] = "PROJECTCHRONO"
        self.cpp_info.names["cmake_find_package_multi"] = "projectchrono"
