from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
import fnmatch
import glob


def apply_patches(source, dest):
    for root, _dirnames, filenames in os.walk(source):
        for filename in fnmatch.filter(filenames, '*.patch'):
            patch_file = os.path.join(root, filename)
            dest_path = os.path.join(dest, os.path.relpath(root, source))
            tools.patch(base_path=dest_path, patch_file=patch_file)


def rename(pattern, name):
    for extracted in glob.glob(pattern):
        os.rename(extracted, name)


class OgreConan(ConanFile):
    name = "ogre"
    version = "1.12.7"
    description = "Open Source 3D Graphics Engine"
    folder = 'ogre-v' + version
    install_path = os.path.join('_build', folder, 'sdk')
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "with_cg": [True, False],
        "with_rendersystem_d3d9": [True, False],
        "with_rendersystem_d3d11": [True, False],
        "with_rendersystem_gl3plus": [True, False],
        "with_rendersystem_gl": [True, False],
        "with_rendersystem_gles2": [True, False],
    }
    default_options = {
        "shared": True,
        "with_cg": True,
        "freetype:shared": False,
        "with_rendersystem_gl3plus": True,
        "with_rendersystem_gl": True,
        "with_rendersystem_gles2": False,
    }
    exports_sources = ['patches*']
    requires = (
        "freeimage/3.18.0@sixten-hilborn/stable",
        "freetype/2.10.1",
        "libpng/1.6.37",  # override freetype's libpng
        "zlib/1.2.11"
    )
    url = "http://github.com/sixten-hilborn/conan-ogre"
    license = "https://opensource.org/licenses/mit-license.php"

    short_paths = True
    
    def config_options(self):
        if self.options.with_rendersystem_d3d9 == None:
            self.options.with_rendersystem_d3d9 = False

        if self.settings.os == 'Windows':
            if self.options.with_rendersystem_d3d11 == None:
                self.options.with_rendersystem_d3d11 = True
        else:
            if self.options.with_rendersystem_d3d11 == None:
                self.options.with_rendersystem_d3d11 = False

    def configure(self):
        if 'x86' not in str(self.settings.arch):
            self.options.with_cg = False

    def requirements(self):
        if self.options.with_cg:
            self.requires("Cg/3.1@sixten-hilborn/stable")

    def build_requirements(self):
        if self.settings.os == 'Linux':
            installer = tools.SystemPackageTool(conanfile=self)
            if self._with_opengl():
                installer.install('libgl1-mesa-dev')
                installer.install('libglu1-mesa-dev')
            if self.options.with_rendersystem_gles2:
                installer.install('libgles2-mesa-dev')

    def system_requirements(self):
        if self.settings.os == 'Linux':
            installer = tools.SystemPackageTool(conanfile=self)
            installer.install("libxmu-dev")
            installer.install("libxaw7-dev")
            installer.install("libxt-dev")
            installer.install("libxrandr-dev")

    def source(self):
        tools.get("https://github.com/OGRECave/ogre/archive/v{0}.zip".format(self.version), sha256='531ff3af813d6833c1b3cd565c54dcebe4e84b4069fd64b59cea141a5f526704')
        rename('ogre-*', self.folder)

    def build(self):
        apply_patches('patches', self.folder)
        tools.replace_in_file(
            '{0}/OgreMain/CMakeLists.txt'.format(self.folder),
            '${ZZip_LIBRARIES}',
            'CONAN_PKG::zlib')
        tools.replace_in_file(
            '{0}/OgreMain/CMakeLists.txt'.format(self.folder),
            'list(APPEND LIBRARIES ZLIB::ZLIB)',
            '')
        tools.replace_in_file(
            '{0}/Components/Overlay/CMakeLists.txt'.format(self.folder),
            '${FREETYPE_LIBRARIES}',
            'CONAN_PKG::freetype')
        tools.replace_in_file(
            '{0}/Components/Overlay/CMakeLists.txt'.format(self.folder),
            'ZLIB::ZLIB',
            'CONAN_PKG::zlib')
        tools.replace_in_file(
            '{0}/PlugIns/FreeImageCodec/CMakeLists.txt'.format(self.folder),
            '${FreeImage_LIBRARIES}',
            'CONAN_PKG::freeimage')
        tools.replace_in_file(
            '{0}/PlugIns/DotScene/CMakeLists.txt'.format(self.folder),
            'pugixml',
            'CONAN_PKG::pugixml')

        # Fix for static build without DirectX 9
        if not self.options.with_rendersystem_d3d9:
            tools.replace_in_file('{0}/Components/Bites/CMakeLists.txt'.format(self.folder), ' ${DirectX9_INCLUDE_DIR}', '')

        #tools.replace_in_file('{0}/PlugIns/CgProgramManager/include/OgreCgPlugin.h'.format(self.folder), '#include "OgrePlugin.h"', '#include <OGRE/OgrePlugin.h>')

        cmake = CMake(self)
        cmake.definitions['CMAKE_INSTALL_PREFIX'] = os.path.join(os.getcwd(), self.install_path)
        cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = True
        cmake.definitions['OGRE_STATIC'] = not self.options.shared
        cmake.definitions['OGRE_COPY_DEPENDENCIES'] = False
        # cmake.definitions['OGRE_UNITY_BUILD'] = True  # Speed up build
        cmake.definitions['OGRE_BUILD_DEPENDENCIES'] = False  # Dependencies should be handled via Conan instead :)
        cmake.definitions['OGRE_BUILD_SAMPLES'] = False
        cmake.definitions['OGRE_BUILD_TESTS'] = False
        cmake.definitions['OGRE_BUILD_TOOLS'] = False
        cmake.definitions['OGRE_INSTALL_PDB'] = False
        cmake.definitions['OGRE_BUILD_RENDERSYSTEM_D3D9'] = self.options.with_rendersystem_d3d9
        cmake.definitions['OGRE_BUILD_RENDERSYSTEM_D3D11'] = self.options.with_rendersystem_d3d11
        cmake.definitions['OGRE_BUILD_RENDERSYSTEM_GL3PLUS'] = self.options.with_rendersystem_gl3plus
        cmake.definitions['OGRE_BUILD_RENDERSYSTEM_GL'] = self.options.with_rendersystem_gl
        cmake.definitions['OGRE_BUILD_RENDERSYSTEM_GLES2'] = self.options.with_rendersystem_gles2
        if self.settings.compiler == 'Visual Studio':
            cmake.definitions['OGRE_CONFIG_STATIC_LINK_CRT'] = str(self.settings.compiler.runtime).startswith('MT')
        cmake.configure(build_folder='_build', source_folder=self.folder)
        cmake.build(target='install')

    def package(self):
        sdk_dir = self.install_path
        include_dir = os.path.join(sdk_dir, 'include', 'OGRE')
        lib_dir = os.path.join(sdk_dir, 'lib')
        bin_dir = os.path.join(sdk_dir, 'bin')
        self.copy(pattern="*.h", dst="include/OGRE", src=include_dir)
        self.copy("*.lib", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.a", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.so*", dst="lib", src=lib_dir, keep_path=False, links=True)
        self.copy("*.dylib", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.dll", dst="bin", src=bin_dir, keep_path=False)
        # Copy resource file for Windows dialogs
        if not self.options.shared and self.settings.os == 'Windows':
            self.copy("*.res", dst="res", src='_build/Components/Bites', keep_path=False)

    def package_info(self):
        # All plugins must be linked at compile time instead of dynamically loaded for static builds
        if not self.options.shared:
            # Unfortunately some headers assumes the OGRE directory is an include path
            self.cpp_info.includedirs.append('include/OGRE')

            if self.options.with_rendersystem_gl:
                self.cpp_info.libs.append('RenderSystem_GL')
            if self.options.with_rendersystem_gl3plus:
                self.cpp_info.libs.append('RenderSystem_GL3Plus')
            if self.options.with_rendersystem_gles2:
                self.cpp_info.libs.append('RenderSystem_GLES2')
            if self.options.with_rendersystem_d3d9:
                self.cpp_info.libs.append('RenderSystem_Direct3D9')
            if self.options.with_rendersystem_d3d11:
                self.cpp_info.libs.append('RenderSystem_Direct3D11')

            if self._with_opengl():
                self.cpp_info.libs.append('OgreGLSupport')

            if self.options.with_cg:
                self.cpp_info.libs.append('Plugin_CgProgramManager')

            self.cpp_info.libs.extend([
                'Plugin_BSPSceneManager',
                'Plugin_OctreeSceneManager',
                'Plugin_OctreeZone',
                'Plugin_ParticleFX',
                'Plugin_PCZSceneManager',
            ])

        self.cpp_info.libs.extend([
            'OgreMain',
            'OgreOverlay',
            'OgrePaging',
            'OgreProperty',
            'OgreRTShaderSystem',
            'OgreTerrain'
        ])
        # 'OgreBites', OgreHLMS', 'OgreMeshLodGenerator', 'OgreVolume',


        if not self.options.shared: #and self.settings.os == 'Windows':
            self.cpp_info.libs = [lib+'Static' for lib in self.cpp_info.libs]
        #is_apple = (self.settings.os == 'Macos' or self.settings.os == 'iOS')
        if self.settings.build_type == "Debug" and self.settings.os == 'Windows': #not is_apple:
            self.cpp_info.libs = [lib+'_d' for lib in self.cpp_info.libs]

        if not self.options.shared and self.settings.os == 'Windows':
            # Link against resource file for Windows dialogs
            self.cpp_info.sharedlinkflags.append(os.path.join(self.package_folder, self.cpp_info.resdirs[0], 'OgreWin32Resources.res'))
            self.cpp_info.exelinkflags = self.cpp_info.sharedlinkflags

        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('rt')

    def _with_opengl(self):
        return self.options.with_rendersystem_gl or self.options.with_rendersystem_gl3plus
