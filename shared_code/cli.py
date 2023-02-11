import logging

import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli1():
	pass


@cli1.command()
@click.option("-s", "--subreddit", help='Specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+Foo',
			  default="sfwpetite+SFWNextDoorGirls+SFWRedheads",
			  show_default=True,
			  required=True)
@click.option("-t", "--transfer_to_cloud", help='Transfer the data to the cloud', default=False, show_default=True,
			  required=False)
def run_collector(subreddit: str, transfer_to_cloud: bool):
	logging.basicConfig(format=f'|:: Thread:%(threadName)s %(levelname)s ::| %(message)s', level=logging.INFO)
	from shared_code.scripts.get_reddit_data import main
	main(subreddit, transfer_to_cloud)


cli = click.CommandCollection(sources=[cli1])

if __name__ == '__main__':
	cli()
