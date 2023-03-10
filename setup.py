from setuptools import setup
import os


def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
	name="sexy-diffusion",
	version="0.0.1",
	author="AJ Stangl",
	author_email="ajstangl@gmail.com",
	description="A simple wrapper for collecting, transforming, and creating gpt2 models based on reddit users/subreddits",
	license="MIT",
	keywords="GPT2",
	include_package_data=True,
	url="https://example.com",
	packages=[
		'shared_code/scripts',
		'shared_code',
		'shared_code/storage',
		'shared_code/data_collection',
		'shared_code/image_captioning'
	],

	long_description=read('README.md'),
	classifiers=[
		"Topic :: Utilities",
		"License :: MIT License",
	],
	entry_points={
		'console_scripts': [
			'sd-tools = shared_code.cli:cli',
		],
	},
)
