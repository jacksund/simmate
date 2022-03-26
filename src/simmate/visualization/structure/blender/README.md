
# Blender setup

I spent a significant amount of trying to get blender working as a python module, but I don't know enough about make files to package this for general use. For now, it's actually easier to just install Blender manually and have Simmate call it from the command line. It's extra work for the user who will just want to vizualize structures and never use Blender directly, but that's just how it is right now... In the future, I may want to just pay a Blender dev to begin supporting blender as bpy module -- even if its a minimal build specifically for Simmate.


# Past notes on making bpy from source

## Making my own blender bpy module (on Ubuntu 18.04)
Following directions from https://wiki.blender.org/wiki/Building_Blender
1. First we need to install all dependencies used to build the final package
```
sudo apt install git;
sudo apt install build-essential;
snap install cmake --classic;
mkdir ~/blender-git;
cd ~/blender-git;
git clone https://git.blender.org/blender.git;
cd blender;
git submodule update --init --recursive;
git submodule foreach git checkout master;
git submodule foreach git pull --rebase origin master;
cd ~/blender-git/blender/build_files/build_environment;
./install_deps.sh;
```
2. In the file bpy_module.cmake, we need to change the portable setting to 'ON':
```
nano /home/jacksund/blender-git/blender/build_files/cmake/config/bpy_module.cmake;
```
manually edit this line:
```
set(WITH_INSTALL_PORTABLE    ON CACHE BOOL "" FORCE)
```
3. With our settings and dependencies all set up, we can now build blender as a python module. The result will be in /blender-git/build_linux_bpy/bin/
```
cd ~/blender-git/blender;
make bpy;
```
4. Lastly, let's copy the created module into our Anaconda enviornment and remove all these build files.
```
cp -r /home/jacksund/blender-git/build_linux_bpy/bin/* /home/jacksund/anaconda3/envs/jacks_env/lib/python3.7/site-packages/;
sudo rm -r /home/jacksund/blender-git;
```
5. You can now 'import bpy' in your python enviornment! 

## Making my own blender bpy module (on Ubuntu 19.10)
Following directions from https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu and also troubleshooting with https://devtalk.blender.org/t/problem-with-running-blender-as-a-python-module/7367
1. First we need to install all dependencies used to build the final package
```
sudo apt-get update;
sudo apt-get install build-essential git subversion cmake libx11-dev libxxf86vm-dev libxcursor-dev libxi-dev libxrandr-dev libxinerama-dev;
mkdir ~/blender-git;
cd ~/blender-git;
git clone http://git.blender.org/blender.git;
cd ~/blender-git/blender;
make update;
cd ~/blender-git
./blender/build_files/build_environment/install_deps.sh --with-all
```
2. In the file bpy_module.cmake, we need to change the portable setting to 'ON':
```
nano /home/jacksund/blender-git/blender/build_files/cmake/config/bpy_module.cmake;
```
manually edit this line:
```
set(WITH_INSTALL_PORTABLE    ON CACHE BOOL "" FORCE)
```
and add these lines: 
```
set(WITH_MEM_JEMALLOC OFF CACHE BOOL "" FORCE)
set(WITH_MOD_OCEANSIM        OFF CACHE BOOL "" FORCE)

set(FFMPEG_LIBRARIES avformat;avcodec;avutil;avdevice;swscale;swresample;lzma;rt;theora;theoradec;theoraenc;vorbis;vorbisenc;vorbisfile;ogg;xvidcore;vpx;opus;mp3lame;x264;openjp2 CACHE STRING "" FORCE)

set(PYTHON_VERSION 3.7 CACHE STRING "" FORCE)
set(LLVM_VERSION 6.0 CACHE STRING "" FORCE)

set(OPENCOLORIO_ROOT_DIR /opt/lib/ocio CACHE STRING "" FORCE)
set(OPENIMAGEIO_ROOT_DIR /opt/lib/oiio CACHE STRING "" FORCE)
set(OSL_ROOT_DIR /opt/lib/osl CACHE STRING "" FORCE)
set(OPENSUBDIV_ROOT_DIR /opt/lib/osd CACHE STRING "" FORCE)
set(OPENCOLLADA_ROOT_DIR /opt/lib/opencollada CACHE STRING "" FORCE)
set(EMBREE_ROOT_DIR /opt/lib/embree CACHE STRING "" FORCE)
set(OPENIMAGEDENOISE_ROOT_DIR /opt/lib/oidn CACHE STRING "" FORCE)
set(ALEMBIC_ROOT_DIR /opt/lib/alembic CACHE STRING "" FORCE)
```
3. With our settings and dependencies all set up, we can now build blender as a python module. The result will be in /blender-git/build_linux_bpy/bin/
```
cd ~/blender-git/blender;
make bpy;
```
4. Lastly, let's copy the created module into our Anaconda environment and remove all these build files.
```
cp -r /home/jacksund/blender-git/build_linux_bpy/bin/* /home/jacksund/anaconda3/envs/jacks_env/lib/python3.7/site-packages/;
sudo rm -r /home/jacksund/blender-git;
```
5. You can now 'import bpy' in your python environment! 
