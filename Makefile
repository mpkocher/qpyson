doc:
	 R -e "rmarkdown::render('README.Rmd')"

formatter:
	black .

clean:
	rm -rf dist build *.egg-info

package:
	python3 setup.py sdist bdist_wheel

deploy-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

deploy:
	twine upload dist/*
