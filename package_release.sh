#!sh
rm -rf ../Package/src
mkdir -p ../Package/src
git archive --format=tar --prefix Dodopult/ HEAD | (cd ../Package/src && tar xf -)
rm -rf dist
rm -rf ../Package/release/Dodopult
/c/Python26/python.exe setup.py py2exe
mv dist ../Package/release/Dodopult