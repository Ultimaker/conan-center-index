from conan import ConanFile
from conan.errors import ConanException
from conan.tools.microsoft import is_msvc
from conan.tools.gnu.get_gnu_triplet import _get_gnu_triplet


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    test_type = "explicit"
    win_bash = True

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)
        # TODO: check if this is is a correct way to check if msys2 is needed
        if self.settings.get_safe("os") == "Windows" and is_msvc(self) and self.win_bash:
            self.tool_requires("msys2/cci.latest")

    def test(self):
        triplet = _get_gnu_triplet(str(self.settings.os), str(self.settings.arch), str(self.settings.compiler))
        self.run("config.guess", run_environment=True, env="conanbuild")
        try:
            self.run(f"config.sub {triplet}", run_environment=True, env="conanbuild")
        except ConanException:
            self.output.info("Current configuration is not supported by GNU config.\nIgnoring...")
