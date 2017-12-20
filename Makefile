install:
	 virtualenv -p python3 --prompt='PSO' ./.env &&\
	 . ./.env/bin/activate &&\
	 pip3 install -r ./requirements.txt &&\
	 echo "[===DONE===]"

test: 
	. ./.env/bin/activate && \
	nosetests --with-coverage --cover-erase --cover-package=pso
