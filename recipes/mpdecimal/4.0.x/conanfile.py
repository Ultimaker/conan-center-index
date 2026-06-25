from conan import ConanFile
from conan.tools.files import get, copy, save, rm, rmdir
from conan.tools.microsoft import MSBuild, is_msvc, MSBuildDeps, MSBuildToolchain
from conan.tools.env import VirtualBuildEnv
from conan.errors import ConanInvalidConfiguration
from conan.tools.layout import basic_layout
import os


class MpdecimalConan(ConanFile):
    name = "mpdecimal"
    description = "mpdecimal is a package for correctly-rounded arbitrary precision decimal floating point arithmetic"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.bytereef.org/mpdecimal/"
    topics = ("decimal", "arithmetic", "math")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cxx": [True, False]
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "cxx": True
    }

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.cxx:
            self.settings.rm_safe("compiler.cppstd")
            self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        # ARM64 Windows support was added in version 4.0.0
        if self.settings.os == "Windows" and self.settings.arch == "armv8":
            if not is_msvc(self):
                raise ConanInvalidConfiguration(f"mpdecimal {self.version} ARM64 Windows requires MSVC compiler")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if is_msvc(self):
            tc = MSBuildToolchain(self)
            tc.generate()

            deps = MSBuildDeps(self)
            deps.generate()
        else:
            # For non-MSVC, we'll use the configure script
            env = VirtualBuildEnv(self)
            env.generate()

    def build(self):
        if is_msvc(self):
            self._build_msvc()
        else:
            self._build_configure()

    def _build_msvc(self):
        # Use the ARM64 build script for ARM64 Windows
        if self.settings.arch == "armv8":
            build_script = "vcbuild_arm64.bat"
        elif self.settings.arch == "x86":
            build_script = "vcbuild32.bat"
        else:  # x86_64
            build_script = "vcbuild64.bat"

        # Change to vcbuild directory and run the appropriate build script
        vcbuild_dir = os.path.join(self.source_folder, "vcbuild")
        self.run(f"{build_script}", cwd=vcbuild_dir)

    def _build_configure(self):
        # For Unix-like systems, use the configure script
        configure_args = [
            f"--prefix={self.package_folder.replace(chr(92), '/')}",
            f"--enable-shared={str(self.options.shared).lower()}",
            f"--enable-cxx={str(self.options.cxx).lower()}"
        ]

        if self.options.get_safe("fPIC", True):
            configure_args.append("--with-pic")

        self.run(f"./configure {' '.join(configure_args)}")
        self.run(f"make -j{os.cpu_count()}")

    def package(self):
        copy(self, "COPYRIGHT.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        if is_msvc(self):
            self._package_msvc()
        else:
            self._package_configure()

    def _package_msvc(self):
        # For MSVC builds, copy the built libraries and headers directly from libmpdec and libmpdec++
        libmpdec_dir = os.path.join(self.source_folder, "libmpdec")
        libmpdecpp_dir = os.path.join(self.source_folder, "libmpdec++")

        # Copy libraries - vcbuild creates both static and shared, so be selective
        if self.options.shared:
            # For shared builds, copy DLLs and import libraries
            copy(self, f"libmpdec-{self.version}.dll", src=libmpdec_dir, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            copy(self, f"libmpdec-{self.version}.dll.lib", src=libmpdec_dir, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        else:
            # For static builds, copy only static libraries (exclude .dll.lib)
            copy(self, f"libmpdec-{self.version}.lib", src=libmpdec_dir, dst=os.path.join(self.package_folder, "lib"), keep_path=False)

        # Copy all header files (mpdecimal.h and any vc-specific headers)
        copy(self, "mpdecimal*.h", src=libmpdec_dir, dst=os.path.join(self.package_folder, "include"), keep_path=False)
        copy(self, "vc*.h", src=libmpdec_dir, dst=os.path.join(self.package_folder, "include"), keep_path=False, excludes=["vctest.h"])
        
        if self.options.cxx:
            if self.options.shared:
                copy(self, f"libmpdec++-{self.version}.dll", src=libmpdecpp_dir, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
                copy(self, f"libmpdec++-{self.version}.dll.lib", src=libmpdecpp_dir, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            else:
                copy(self, f"libmpdec++-{self.version}.lib", src=libmpdecpp_dir, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            copy(self, "decimal.hh", src=libmpdecpp_dir, dst=os.path.join(self.package_folder, "include"), keep_path=False)

    def _package_configure(self):
        # For configure builds, use make install
        self.run("make install")

    def package_info(self):
        # Use components like the 2.5.x version
        if is_msvc(self):
            lib_prefix = "lib"
            if self.options.shared:
                lib_suffix = f"-{self.version}.dll"
            else:
                lib_suffix = f"-{self.version}"
        else:
            lib_prefix = ""
            lib_suffix = ""

        self.cpp_info.components["libmpdecimal"].libs = [f"{lib_prefix}mpdec{lib_suffix}"]
        
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libmpdecimal"].system_libs = ["m"]

        if self.options.cxx:
            self.cpp_info.components["libmpdecimal++"].libs = [f"{lib_prefix}mpdec++{lib_suffix}"]
            self.cpp_info.components["libmpdecimal++"].requires = ["libmpdecimal"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["libmpdecimal++"].system_libs = ["pthread"]
