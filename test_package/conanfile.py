#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from os import path

class GNGeneratorTestPackage(ConanFile):
    settings = "os", "compiler", "arch", "build_type"
    generators = "GNGenerator"

    def build_requirements(self):
        self.build_requires("GNGenerator/0.1@conan/stable")


    def requirements(self):
        self.requires("gtest/1.8.1@bincrafters/stable")

    def build(self):
        release_folder = "build-dir/release"
        tools.mkdir(release_folder)
        with tools.chdir(release_folder):
            self.run("ls -l")


    def test(self):
        #self.run("ls -l")
        #generated_file = [path.join("gtest", "BUILD.gn")]
        #for f in generated_file:
        #    print('#' * (len(f) + 4))
        #    print("# {filename} #".format(filename=f))
        #    print('#' * (len(f) + 4))
        #    with open(f, "r") as fd:
        #        print(fd.read())
        pass
