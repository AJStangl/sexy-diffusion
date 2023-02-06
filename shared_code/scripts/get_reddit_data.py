import logging

from shared_code.data_collection.reddit_data_collector import RedditDataCollector

if __name__ == '__main__':
	logging.basicConfig(format=f'|:: Thread:%(threadName)s %(levelname)s ::| %(message)s', level=logging.INFO)
	builder = RedditDataCollector()
	builder.download_subreddit_images("sfwpetite+SFWNextDoorGirls+SFWRedheads")

	captioned_items_to_stage = builder.update_with_ai_captions()

	builder.move_to_staging(captioned_items_to_stage)
	builder.write_json_meta_data(captioned_items_to_stage)
	builder.move_training_to_cloud()
