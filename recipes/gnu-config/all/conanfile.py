from pathlib import Path

from conan import ConanFile
from conan.tools.layout import basic_layout
from conan.tools.files import get, load, save, copy
from conan.errors import ConanException

required_conan_version = ">=1.50.0"


class GnuConfigConan(ConanFile):
    name = "gnu-config"
    description = "The GNU config.guess and config.sub scripts"
    homepage = "https://savannah.gnu.org/projects/config/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("gnu", "config", "autotools", "canonical", "host", "build", "target", "triplet")
    license = "GPL-3.0-or-later", "autoconf-special-exception"
    generators = "AutotoolsToolchain"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="source")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _extract_license(self):
        txt_lines = load(self, Path(self.source_folder, "config.guess")).splitlines()
        start_index = None
        end_index = None
        for line_i, line in enumerate(txt_lines):
            if start_index is None:
                if "This file is free" in line:
                    start_index = line_i
            if end_index is None:
                if "Please send patches" in line:
                    end_index = line_i
        if not all((start_index, end_index)):
            raise ConanException("Failed to extract the license")
        return "\n".join(txt_lines[start_index:end_index])

    def package(self):
        save(self, Path(self.package_folder, "licenses", "COPYING"), self._extract_license())
        copy(self, "config.*", src=self.source_folder, dst=Path(self.package_folder, "bin"))

    def package_info(self):
        bin_path = Path(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.buildenv_info.prepend_path("PATH", bin_path)

        self.conf_info.define("user.gnu-config:guess", str(Path(bin_path, "config.guess")))
        self.conf_info.define("user.gnu-config:sub", str(Path(bin_path, "config.sub")))

    def package_id(self):
        self.info.header_only()
