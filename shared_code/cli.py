import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli1():
	pass

@cli1.command()
@click.option("-s", "--subreddit", help='Specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+Foo',
			  default="",
			  show_default=True,
			  required=True)
def run_collector(subreddit: str):
	from shared_code.scripts.get_reddit_data import main
	main(subreddit)


cli = click.CommandCollection(sources=[cli1])

if __name__ == '__main__':
	cli()
