tests:
	PYTHONPATH=./src nosetests

init:
	conda env create -f environment.yml

update:
	conda env update -f environment.yml
