import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli1():
	pass


@cli1.command()
@click.option("-r", "--run",
			  help='runs a thing',
			  default="",
			  show_default=True, required=True)
@click.option("-s", "--sub-reddit",
			  help='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse',
			  default='CoopAndPabloPlayHouse', show_default=True, required=True)
def run_process(bot_names: str, sub_reddit: str):
	print(bot_names, sub_reddit)




cli = click.CommandCollection(sources=[cli1])

if __name__ == '__main__':
	cli()
