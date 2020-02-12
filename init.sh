case "$(uname -s)" in
   Darwin)
     echo "MAC OS detected"
     MAC_OS=1;;
   Linux)
     echo "LINUX detected"
     LINUX=1;;
   CYGWIN*|MINGW32*|MSYS*)
     echo "WIN detected"
     WIN=1;;
   *)
     echo 'other OS' 
     ;;
esac

if [[ ${LINUX} ]]; 
then 
    apt-get update
    apt-get install python2.7
    apt-get install virtualenv
    apt-get install python-pip

    # для Instagram-API-python и moviepy
    apt-get install ffmpeg
fi

if [[ ${MAC_OS} ]]; 
then 
    apt-get update
    apt-get install python2.7
    apt-get install virtualenv
    apt-get install python-pip
    
    sudo apt-get install PIL
    sudo brew install libjpeg
fi

pip install --upgrade pip
pip install -r requirements.txt

echo "=== instagram-explore === "
if [ ! -d "instagram-explore" ]; then
    git clone https://github.com/midnightSuyama/instagram-explore.git
    cd instagram-explore
    python setup.py build && python setup.py install
    cd ..
else
    cd instagram-explore
    
    if [ "`git log --pretty=%H ...refs/heads/master^ | head -n 1`" = "`git ls-remote origin -h refs/heads/master |cut -f1`" ] ; then
        echo "up to date"
    else
        echo "not up to date"
        git fetch && git rebase origin/master
        python setup.py build && python setup.py install
        cd ..
    fi
fi

echo "=== Instagram-API-python === "
if [ ! -d "Instagram-API-python" ]; then
    git clone https://github.com/LevPasha/Instagram-API-python.git
    cd Instagram-API-python
    python setup.py build && python setup.py install
    cd ..
else
    cd Instagram-API-python
    if [ "`git log --pretty=%H ...refs/heads/master^ | head -n 1`" = "`git ls-remote origin -h refs/heads/master |cut -f1`" ] ; then
        echo "up to date"
    else
        echo "not up to date"
        git fetch && git rebase origin/master
        python setup.py build && python setup.py install
        cd ..
    fi
fi

