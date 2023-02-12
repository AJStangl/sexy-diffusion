import logging

from shared_code.data_collection.reddit_data_collector import RedditDataCollector


def main(subreddits: str, transfer_to_cloud: bool):
	logging.basicConfig(format=f'|:: Thread:%(threadName)s %(levelname)s ::| %(message)s', level=logging.INFO)
	builder = RedditDataCollector()
	builder.download_subreddit_images(subreddits)

	builder.update_with_ai_captions()

	if transfer_to_cloud:
		builder.move_to_staging()
		# builder.move_training_to_cloud()