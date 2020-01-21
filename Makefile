doc:
	 R -e "rmarkdown::render('README.Rmd')"

formatter:
	black .
