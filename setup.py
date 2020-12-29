import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setuptools.setup(
	name="labtool",
	version="0.0.18",
	author="Alejandro Caravaca Puchades",
	author_email="acaravacapuchades+dev@gmail.com",
	description="A tool to analyze lab report files",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/acpuchades/libtool",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"Operating System :: OS Independent",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
	],
	python_requires='>=3.6',
	entry_points={
		"console_scripts": [
			"labtool = labtool.__main__:main"
		]
	},
)
