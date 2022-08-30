from pathlib import Path

from conans.client.subsystems import deduce_subsystem, subsystem_path

from conan import ConanFile
from conan.tools.files import get, AutoPackager, replace_in_file, apply_conandata_patches, rmdir
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.gnu import Autotools
from conan.tools.scm import Version

required_conan_version = ">=1.50.0"


class AutomakeConan(ConanFile):
    name = "automake"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gnu.org/software/automake/"
    description = "Automake is a tool for automatically generating Makefile.in files compliant with the GNU Coding Standards."
    topics = ("conan", "automake", "configure", "build")
    license = ("GPL-2.0-or-later", "GPL-3.0-or-later")
    settings = "os", "arch", "compiler", "build_type"
    generators = "AutotoolsDeps", "AutotoolsToolchain"
    win_bash = True

    exports_sources = "patches/*"

    def build_requirements(self):
        if hasattr(self, "settings_build"):
            self.build_requires("autoconf/2.71")
        # TODO: check if this is is a correct way to check if msys2 is needed
        if self.settings.get_safe("os") == "Windows" and is_msvc(self) and self.win_bash:
            self.tool_requires("msys2/cci.latest")

    def layout(self):
        basic_layout(self, src_folder="source")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        self.run("autoconf --version", run_environment=True)
        apply_conandata_patches(self)
        if self.settings.os == "Windows":
            # tracing using m4 on Windows returns Windows paths => use cygpath to convert to unix paths
            replace_in_file(self, Path(self.source_folder, "bin", "aclocal.in"),
                                               "          $map_traced_defs{$arg1} = $file;",
                                               "          $file = `cygpath -u $file`;\n"
                                               "          $file =~ s/^\\s+|\\s+$//g;\n"
                                               "          $map_traced_defs{$arg1} = $file;")
        autotool = Autotools(self)
        autotool.configure()
        autotool.make()
        subsystem = deduce_subsystem(self, scope="build")
        install_path = subsystem_path(subsystem, self.package_folder)
        autotool.install(args=[f"DESTDIR={install_path}"])

    def package(self):
        packager = AutoPackager(self)
        packager.run()
        rmdir(self, Path(self.package_folder, "share", "info"))
        rmdir(self, Path(self.package_folder, "share", "man"))
        rmdir(self, Path(self.package_folder, "share", "doc"))

    def package_info(self):
        bin_path = Path(self.package_folder, "bin")
        self.output.info(f"Appending PATH env var with : {bin_path}")
        self.buildenv_info.append_path("PATH", str(bin_path))

        aclocal = Path(self.package_folder, "bin", "aclocal")
        self.output.info(f"Appending ACLOCAL environment variable with: {aclocal}")
        self.buildenv_info.define_path("ACLOCAL",  str(aclocal))

        automake_datadir = Path(self._datarootdir)
        self.output.info(f"Setting AUTOMAKE_DATADIR to {automake_datadir}")
        self.buildenv_info.define_path("AUTOMAKE_DATADIR", str(automake_datadir))

        automake_libdir = Path(self._automake_libdir)
        self.output.info(f"Setting AUTOMAKE_LIBDIR to {automake_libdir}")
        self.buildenv_info.define_path("AUTOMAKE_LIBDIR", str(automake_libdir))

        automake_perllibdir = Path(self._automake_libdir)
        self.output.info("Setting AUTOMAKE_PERLLIBDIR to {}".format(automake_perllibdir))
        self.buildenv_info.define_path("AUTOMAKE_PERLLIBDIR", str(automake_perllibdir))

        automake = Path(self.package_folder, "bin", "automake")
        self.output.info(f"Setting AUTOMAKE to {automake}")
        self.buildenv_info.define_path("AUTOMAKE", str(automake))

    @property
    def _datarootdir(self):
        return Path(self.package_folder, "share")

    @property
    def _automake_libdir(self):
        version = Version(self.version)
        return Path(self._datarootdir, f"automake-{version.major}.{version.minor}")
