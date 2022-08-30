from pathlib import Path

from conan import ConanFile
from conan.tools.files import get, AutoPackager, apply_conandata_patches
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.gnu import Autotools

from conans.client.subsystems import deduce_subsystem, subsystem_path

required_conan_version = ">=1.50.0"


class AutoconfConan(ConanFile):
    name = "autoconf"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gnu.org/software/autoconf/"
    description = "Autoconf is an extensible package of M4 macros that produce shell scripts to automatically configure software source code packages"
    topics = ("autoconf", "configure", "build")
    license = ("GPL-2.0-or-later", "GPL-3.0-or-later")
    settings = "os", "arch", "compiler", "build_type"
    generators = "AutotoolsDeps", "AutotoolsToolchain"
    win_bash = True

    exports_sources = "patches/*"

    def build_requirements(self):
        # TODO: check if this is is a correct way to check if msys2 is needed
        if self.settings.get_safe("os") == "Windows" and is_msvc(self) and self.win_bash:
            self.tool_requires("msys2/cci.latest")

    def requirements(self):
        self.requires("m4/1.4.19")

    def layout(self):
        basic_layout(self, src_folder="source")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        apply_conandata_patches(self)
        autotool = Autotools(self)
        autotool.configure()
        autotool.make()
        subsystem = deduce_subsystem(self, scope="build")
        install_path = subsystem_path(subsystem, self.package_folder)
        autotool.install(args=[f"DESTDIR={install_path}"])

    def package(self):
        packager = AutoPackager(self)
        packager.run()

    def package_info(self):
        bin_path = Path(self.package_folder, "bin")
        self.output.info(f"Appending PATH env var with : {bin_path}")
        self.buildenv_info.append_path("PATH", str(bin_path))

        ac_macrodir = self._autoconf_datarootdir
        self.output.info(f"Setting AC_MACRODIR to {ac_macrodir}")
        self.buildenv_info.define_path("AC_MACRODIR", str(ac_macrodir))

        autoconf = Path(self.package_folder, "bin", "autoconf")
        self.output.info(f"Setting AUTOCONF to {autoconf}")
        self.buildenv_info.define_path("AUTOCONF", str(autoconf))

        autoreconf = Path(self.package_folder, "bin", "autoreconf")
        self.output.info(f"Setting AUTORECONF to {autoreconf}")
        self.buildenv_info.define_path("AUTORECONF", str(autoreconf))

        autoheader = Path(self.package_folder, "bin", "autoheader")
        self.output.info(f"Setting AUTOHEADER to {autoheader}")
        self.buildenv_info.define_path("AUTOHEADER", str(autoheader))

        autom4te = Path(self.package_folder, "bin", "autom4te")
        self.output.info(f"Setting AUTOM4TE to {autom4te}")
        self.buildenv_info.define_path("AUTOM4TE", str(autom4te))

        autom4te_perllibdir = self._autoconf_datarootdir
        self.output.info(f"Setting AUTOM4TE_PERLLIBDIR to {autom4te_perllibdir}")
        self.buildenv_info.define_path("AUTOM4TE_PERLLIBDIR", str(autom4te_perllibdir))

    @property
    def _datarootdir(self):
        return Path(self.package_folder, "bin", "share")

    @property
    def _autoconf_datarootdir(self):
        return Path(self._datarootdir, "autoconf")
