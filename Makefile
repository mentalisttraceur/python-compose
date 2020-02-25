default:
	python setup.py sdist bdist_wheel --universal

clean:
	rm -rf __pycache__ *.py[oc] build *.egg-info dist
