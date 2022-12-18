from conan import ConanFile
from conan.tools.build import check_min_cppstd, valid_min_cppstd
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rm, replace_in_file
from conan.tools.layout import basic_layout
import os


required_conan_version = ">=1.53.0"


class PackageConan(ConanFile):
    name = "vtu11"
    description = "Vtu11 is a small C++ header-only library to write unstructured grids using the vtu file format"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/phmkopp/vtu11"
    topics = ("vtu", "c++11")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_zlib": [True, False],
    }
    default_options = {
        "with_zlib": True,
    }

    @property
    def _min_cppstd(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.13", transitive_headers=True)

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "vtu11", "impl", "zlibWriter_impl.hpp"), "uLong", "size_t", strict=False)
        if valid_min_cppstd(self, 17):
            rm(self, "filesystem.hpp", os.path.join(self.source_folder, "vtu11", "inc"))

    def build(self):
        self._patch_sources()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            pattern="*.hpp",
            dst=os.path.join(self.package_folder, "include", "vtu11"),
            src=os.path.join(self.source_folder, "vtu11"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if not valid_min_cppstd(self, 17):
            self.cpp_info.cxxflags = ["-std=c++11"]

        if self.options.with_zlib:
            self.cpp_info.defines = ["VTU11_ENABLE_ZLIB"]

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "vtu11"
        self.cpp_info.filenames["cmake_find_package_multi"] = "vtu11"
        self.cpp_info.names["cmake_find_package"] = "vtu11"
        self.cpp_info.names["cmake_find_package_multi"] = "vtu11"
