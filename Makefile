all: html pdf

html: DESCRIPTION.rst
	rst2html DESCRIPTION.rst > DESCRIPTION.html

latex: DESCRIPTION.rst
	rst2latex DESCRIPTION.rst > DESCRIPTION.tex

pdf: latex
	pdflatex -output-dir /tmp DESCRIPTION.tex
	pdflatex -output-dir /tmp DESCRIPTION.tex
	pdflatex -output-dir /tmp DESCRIPTION.tex
	cp /tmp/DESCRIPTION.pdf ./DESCRIPTION.pdf
