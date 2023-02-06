import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli1():
	pass


cli = click.CommandCollection(sources=[])

if __name__ == '__main__':
	cli()
