from os import path
from conans import ConanFile, tools


class GNConanFile(ConanFile):
    name = "GN"
    version = "master"
    description = """GN is a meta-build system that generates build files for Ninja."""
    license = "Google license, variation a BSD-3-clause (https://opensource.org/licenses/bsd-license.php)"
    url = "https://gn.googlesource.com/gn"
    settings = "os", "compiler", "arch", "build_type"
    source_dir = "{name}-{version}".format(name=name, version=version)
    options = {
        "tests": [True, False]
    }
    default_options = {
        "tests": False
    }
    scm = {
        "type": "git",
        "subfolder": source_dir,
        "url": url,
        "revision": version
    }

    def source(self):
        pass

    def build(self):
        with tools.chdir(self.source_dir):
            build_dir = path.join(self.build_folder, "build-dir")

            if self.settings.os == "Windows":
                python_executable = "C:\\Python27\\python.exe"
                build_env = tools.vcvars_dict(self.settings)
            else:
                python_executable = "python2.7"
                build_env = dict()
                build_env["LDFLAGS"] = "-fuse-ld=gold"

            with tools.environment_append(build_env):
                self.run("{python} build/gen.py --out-path={build_dir}"\
                         .format(python=python_executable, build_dir=build_dir))
                self.run("ninja -j {cpu_nb} -C {build_dir}"\
                    .format(cpu_nb=tools.cpu_count()-1, build_dir=build_dir))
                if self.options.tests:
                    self.run("{build_dir}/gn_unittests".format(build_dir=build_dir))

    def package(self):
        gn_executable = "gn.exe" if self.settings.os == "Windows" else "gn"
        self.copy(gn_executable, dst="bin", src="build-dir", keep_path=False)

    def package_info(self):
        self.cpp_info.bindirs = ['bin']

    def deploy(self):
        self.copy("*", keep_path=True)
