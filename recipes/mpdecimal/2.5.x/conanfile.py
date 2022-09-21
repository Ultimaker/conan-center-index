import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv, VirtualBuildEnv
from conan.tools.files import copy, get, chdir, apply_conandata_patches, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.51.3"


class MpdecimalConan(ConanFile):
    name = "mpdecimal"
    description = "mpdecimal is a package for correctly-rounded arbitrary precision decimal floating point arithmetic."
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.bytereef.org/mpdecimal"
    topics = ("mpdecimal", "multiprecision", "library")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cxx": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cxx": True,
    }

    @property
    def _settings_build(self):
        # TODO: Remove or Conan v2
        return getattr(self, "setings_build", self.settings)

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    def export_sources(self):
        for p in self.conan_data.get("patches", {}).get(self.version, []):
            copy(self, p["patch_file"], self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            try:
                del self.options.fPIC
            except ValueError:
                pass
        if not self.options.cxx:
            try:
                del self.settings.compiler.libcxx
            except ValueError:
                pass
            try:
                del self.settings.compiler.cppstd
            except ValueError:
                pass

    def layout(self):
        basic_layout(self, src_folder="src")  # src_folder must use the same source folder name the project

    def validate(self):
        if is_msvc(self) and self.settings.arch not in ("x86", "x86_64"):
            raise ConanInvalidConfiguration("Arch is unsupported")
        if self.options.cxx:
            if self.options.shared and self.settings.os == "Windows":
                raise ConanInvalidConfiguration("A shared libmpdec++ is not possible on Windows (due to non-exportable thread local storage)")

    def build_requirements(self):
        if self.win_bash and not self.conf.get("tools.microsoft.bash:path", default=False, check_type=bool):
            self.build_requires("msys2/cci.latest")
        if not is_msvc(self):
            self.build_requires("automake/1.16.4")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def _build_msvc(self):
        libmpdec_folder = os.path.join(self.build_folder, self.source_folder, "libmpdec")
        libmpdecpp_folder = os.path.join(self.build_folder, self.source_folder, "libmpdec++")
        vcbuild_folder = os.path.join(self.build_folder, self.source_folder, "vcbuild")
        arch_ext = f"{32 if self.settings.arch == 'x86' else 64}"
        dist_folder = os.path.join(vcbuild_folder, f"dist{arch_ext}")
        os.mkdir(dist_folder)

        shutil.copy(os.path.join(libmpdec_folder, "Makefile.vc"), os.path.join(libmpdec_folder, "Makefile"))

        autotools = AutoToolsBuildEnvironment(self)

        mpdec_extra_flags = []
        mpdecxx_extra_flags = []
        if Version(self.version) >= "2.5.1":
            if self.options.shared:
                mpdec_extra_flags = ["-DMPDECIMAL_DLL"]
                mpdecxx_extra_flags = ["-DLIBMPDECXX_DLL"]

        mpdec_target = "libmpdec-{}.{}".format(self.version, "dll" if self.options.shared else "lib")
        mpdecpp_target = "libmpdec++-{}.{}".format(self.version, "dll" if self.options.shared else "lib")

        builds = [[libmpdec_folder, mpdec_target, mpdec_extra_flags] ]
        if self.options.cxx:
            builds.append([libmpdecpp_folder, mpdecpp_target, mpdecxx_extra_flags])
        with tools.vcvars(self):
            for build_dir, target, extra_flags in builds:
                with chdir(self, build_dir):
                    self.run("""nmake /nologo /f Makefile.vc {target} MACHINE={machine} DEBUG={debug} DLL={dll} CONAN_CFLAGS="{cflags}" CONAN_CXXFLAGS="{cxxflags}" CONAN_LDFLAGS="{ldflags}" """.format(
                        target=target,
                        machine={"x86": "ppro", "x86_64": "x64"}[str(self.settings.arch)],  # FIXME: else, use ansi32 and ansi64
                        debug="1" if self.settings.build_type == "Debug" else "0",
                        cflags=" ".join(autotools.flags + extra_flags),
                        cxxflags=" ".join(autotools.cxx_flags + extra_flags),
                        ldflags=" ".join(autotools.link_flags),
                    ))

        with chdir(libmpdec_folder):
            shutil.copy("mpdecimal.h", dist_folder)
            if self.options.shared:
                shutil.copy("libmpdec-{}.dll".format(self.version), os.path.join(dist_folder, "libmpdec-{}.dll".format(self.version)))
                shutil.copy("libmpdec-{}.dll.exp".format(self.version), os.path.join(dist_folder, "libmpdec-{}.exp".format(self.version)))
                shutil.copy("libmpdec-{}.dll.lib".format(self.version), os.path.join(dist_folder, "libmpdec-{}.lib".format(self.version)))
            else:
                shutil.copy("libmpdec-{}.lib".format(self.version), os.path.join(dist_folder, "libmpdec-{}.lib".format(self.version)))
        if self.options.cxx:
            with chdir(self, libmpdecpp_folder):
                shutil.copy("decimal.hh", dist_folder)
                shutil.copy("libmpdec++-{}.lib".format(self.version), os.path.join(dist_folder, "libmpdec++-{}.lib".format(self.version)))

    def generate(self):
        if is_msvc(self):

            pass
        else:
            tc = AutotoolsToolchain(self)
            tc.configure_args.extend([
                "--enable-cxx" if self.options.cxx else "--disable-cxx"
            ])

            env = tc.environment()

            if self.settings.os == "Macos" and self.settings.arch == "armv8":
                env.append("LDFLAGS", " -arch arm64")
                env.define("LDXXFLAGS", "-arch arm64")
            tc.generate(env)

            # generate dependencies for autotools
            tc = AutotoolsDeps(self)
            tc.generate()
            # inject tools_requires env vars in build scope (not needed if there is no tool_requires)
            env = VirtualBuildEnv(self)
            env.generate()
            # inject requires env vars in build scope
            # it's required in case of native build when there is AutotoolsDeps & at least one dependency which might be shared, because configure tries to run a test executable
            if not cross_building(self):
                env = VirtualRunEnv(self)
                env.generate(scope="build")

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            self._build_msvc()
        else:
            autotools = Autotools(self)
            self.run("autoreconf -fiv", cwd=self.source_path, env="conanrun")

            libmpdec, libmpdecpp = self._target_names

            with chdir(self, self.source_path):
                autotools.configure(build_script_folder=self.source_path)

            with chdir(self, self.source_path.joinpath("libmpdec")):
                print("-"*100)
                print(self.run("pwd"))
                autotools.make(target=libmpdec)
            if self.options.cxx:
                with chdir(self, self.source_path.joinpath("libmpdec++")):
                    autotools.make(target=libmpdecpp)

    def package(self):
        copy(self, pattern="LICENSE.txt", src=self.source_folder, dst="licenses")
        if is_msvc(self):
            distfolder = os.path.join(self.build_folder, self.source_folder, "vcbuild", "dist{}".format(32 if self.settings.arch == "x86" else 64))
            copy(self, pattern="vc*.h", src=os.path.join(self.build_folder, self.source_folder, "libmpdec"), dst="include")
            copy(self, pattern="*.h", src=distfolder, dst="include")
            if self.options.cxx:
                copy(self, pattern="*.hh", src=distfolder, dst="include")
            copy(self, pattern="*.lib", src=distfolder, dst="lib")
            copy(self, pattern="*.dll", src=distfolder, dst="bin")
        else:
            autotools = Autotools(self)
            with chdir(self, self.source_path):
                autotools.install()
            rmdir(self, self.package_path.joinpath("share"))


    def package_info(self):
        lib_pre_suf = ("", "")
        if is_msvc(self):
            lib_pre_suf = ("lib", "-{}".format(self.version))
        elif self.settings.os == "Windows" and self.options.shared:
            lib_pre_suf = ("", ".dll")

        self.cpp_info.components["libmpdecimal"].libs = ["{}mpdec{}".format(*lib_pre_suf)]
        if self.options.shared and is_msvc(self):
            if Version(self.version) >= Version("2.5.1"):
                self.cpp_info.components["libmpdecimal"].defines = ["MPDECIMAL_DLL"]
            else:
                self.cpp_info.components["libmpdecimal"].defines = ["USE_DLL"]
        else:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["libmpdecimal"].system_libs = ["m"]

        if self.options.cxx:
            self.cpp_info.components["libmpdecimal++"].libs = ["{}mpdec++{}".format(*lib_pre_suf)]
            self.cpp_info.components["libmpdecimal++"].requires = ["libmpdecimal"]
            if self.options.shared and Version(self.version) >= Version("2.5.1"):
                self.cpp_info.components["libmpdecimal"].defines = ["MPDECIMALXX_DLL"]

    @property
    def _shared_suffix(self):
        if is_apple_os(self.settings.os):
            return ".dylib"
        return {
            "Windows": ".dll",
        }.get(str(self.settings.os), ".so")

    @property
    def _target_names(self):
        libsuffix = self._shared_suffix if self.options.shared else ".a"
        versionsuffix = ".{}".format(self.version) if self.options.shared else ""
        suffix = "{}{}".format(versionsuffix, libsuffix) if is_apple_os(self) or self.settings.os == "Windows" else "{}{}".format(libsuffix, versionsuffix)
        return "libmpdec{}".format(suffix), "libmpdec++{}".format(suffix)
