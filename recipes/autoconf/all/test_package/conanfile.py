from pathlib import Path

from conan import ConanFile
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.gnu import Autotools
from conan.tools.build import cross_building

required_conan_version = ">=1.50.0"


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "AutotoolsDeps", "AutotoolsToolchain"
    test_type = "explicit"
    win_bash = True

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        if self.settings.get_safe("os") == "Windows" and is_msvc(self) and self.win_bash:
            self.tool_requires("msys2/cci.latest")

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        self.output.info(f"tools.microsoft.bash:subsystem: {self.conf.get('tools.microsoft.bash:subsystem')}")

    def layout(self):
        basic_layout(self, src_folder="source")

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def test(self):
        if not cross_building(self):
            self.run(Path(".", "test_package"), run_environment=True)
