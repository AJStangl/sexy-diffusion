import datetime
import hashlib
import logging
import os
import shutil
import time

import pandas
import pandas as pd
import requests
from azure.data.tables import TableClient

from shared_code.image_captioning.bipin import ImageCaption
from shared_code.storage.blob import BlobAdapter
from shared_code.storage.table import TableAdapter
from shared_code.storage.table_entry import TableEntry

logger = logging.getLogger(__name__)
logging.getLogger("azure.storage").setLevel(logging.WARNING)


class RedditDataCollector:
	def __init__(self):
		self.out_path = os.environ["OUT_PATH"]
		self.table_adapter = TableAdapter()
		self.table_client: TableClient = self.table_adapter.get_table_client(
			table_name=os.environ["IMAGE_TRAINING_TABLE"])
		self.image_caption = ImageCaption()
		self.image_count = 0
		self.hashes = []
		self.ids = []

	def loop_between_dates(self, start_datetime, end_datetime):
		time_interval = datetime.timedelta(weeks=1)

		# Make sure the start_datetime is always a Monday by shifting the start back to monday
		start_datetime = start_datetime - datetime.timedelta(days=start_datetime.weekday())

		period_start_date = start_datetime

		while period_start_date < end_datetime:
			period_end_date = min(period_start_date + time_interval, end_datetime)

			yield period_start_date, period_end_date

			if (period_start_date + time_interval) >= end_datetime:
				break

			period_start_date = period_end_date

	def make_entry(self, image, text, submission_id, author, url, flair, permalink, sub, image_hash) -> dict:
		entry = TableEntry(PartitionKey=os.environ["IMAGE_TRAINING_TABLE"], RowKey=submission_id, image=image,
						   text=text, id=submission_id,
						   author=author, url=url, flair=flair, permalink=permalink, subreddit=sub, hash=image_hash,
						   caption=None)
		return entry

	def download_subreddit_images(self, subreddit, start_date="2023-01-01",
								  end_date=datetime.datetime.today().strftime('%Y-%m-%d')):

		all_current_images: list[dict] = list(self.table_client.list_entities())

		self.hashes = [x['hash'] for x in all_current_images]
		self.ids = [x['id'] for x in all_current_images]

		start_date = datetime.datetime.fromisoformat(start_date)

		end_date = datetime.datetime.fromisoformat(end_date)

		subs = subreddit.split("+")
		final_path = os.path.join(self.out_path, subreddit)
		for subreddit in subs:
			logging.info(f"== Starting {subreddit}==")
			for start, end in self.loop_between_dates(start_date, end_date):
				submission_search_link = ('https://api.pushshift.io/reddit/submission/search/'
										  '?subreddit={}&after={}&before={}&stickied=0&limit={}&mod_removed=0')
				submission_search_link = submission_search_link.format(subreddit, int(start.timestamp()),
																	   int(end.timestamp()), 100)
				submission_response = requests.get(submission_search_link)
				try:
					data = submission_response.json()
				except requests.exceptions.JSONDecodeError:
					logging.error("Error decoding JSON")
					continue

				submissions = data.get('data')

				if submissions is None:
					continue
				try:
					os.mkdir(final_path)
				except FileExistsError:
					pass

				for submission in submissions:
					self.handle_submission(submission, data, final_path)

			logging.info(f"All images from {subreddit} subreddit are downloaded")

		logging.info("All images are downloaded: Total count\t{image_count}")

	def handle_submission(self, submission, data, final_path):
		try:
			if 'selftext' not in submission:
				# ignore submissions with no selftext key (buggy)
				return

			if submission['selftext'] in ['[removed]', '[deleted]']:
				# ignore submissions that have no content
				return

			if submission.get('id') in self.ids:
				return

			if "url" in submission:
				image_url = submission['url']
				flair = submission.get('link_flair_text')
				title = submission.get('title')
				submission_id = submission.get('id')
				author = submission.get('author')
				url = submission.get('url')
				permalink = submission.get('permalink')
				subreddit = submission.get('subreddit')

				if image_url.endswith("jpg"):
					# Get the image file name from the URL
					image_name = image_url.split("/")[-1]

					# Download the image and save it to the current directory
					response = requests.get(image_url)

					content = response.content
					md5 = hashlib.md5(content).hexdigest()
					if md5 == "f17b01901c752c1bb04928131d1661af" or md5 == "d835884373f4d6c8f24742ceabe74946" or md5 in self.hashes:
						return
					else:
						self.hashes.append(md5)

					out_image = f"{final_path}/{image_name}"
					try:
						with open(out_image, "wb") as f:
							f.write(content)
							caption = self.image_caption.caption_image(out_image)
							entity = TableEntry(
								PartitionKey='training',
								RowKey=submission_id,
								image=out_image,
								text=title,
								id=submission_id,
								author=author,
								url=url,
								flair=flair,
								permalink=permalink,
								subreddit=subreddit,
								hash=md5,
								caption=caption)
							to_add = entity.__dict__
							logging.info(to_add)
							self.table_client.upsert_entity(entity=to_add)
							self.image_count += 1
							logging.info("File downloaded\t" + image_name + "\t" + "count\t" + str(self.image_count))
							return
					except Exception as e:
						logging.error(e)
						return
			else:
				return

		except Exception as e:
			logging.error(e)
			return

	def update_with_ai_captions(self) -> None:
		caption_generator : ImageCaption= ImageCaption()
		all_current_images: list[dict] = list(self.table_client.list_entities())
		for image in all_current_images:
			if not os.path.exists(image.get('image')):
				logging.info(f"File does not exist, removing from list: {image.get('image')}")
			else:
				if image.get('caption') is not None:
					logging.info(f"Image already has a caption: {image.get('image')}")
					continue
				try:
					image['caption'] = caption_generator.caption_image(image.get('image'))
					image['updated_caption'] = caption_generator.caption_image_vit(image.get('image'))
					self.table_client.upsert_entity(entity=image)
				except Exception as e:
					logging.error(e)
					continue
		return None

	def move_to_staging(self) -> list[dict]:
		training_image_path = os.environ["LOCAL_TRAINING_IMAGES"]
		try:
			os.mkdir(training_image_path)
		except FileExistsError:
			pass

		all_current_images: list[dict] = list(self.table_client.list_entities())
		print("All Current Images: " + str(len(all_current_images)))

		present_images = [item for item in all_current_images if os.path.exists(item.get("image"))]

		print("Present Images: " + str(len(present_images)))

		filtered_on_caption = [item for item in present_images if item.get("caption") is not None]

		print("Filtered on Caption: " + str(len(filtered_on_caption)))

		dataframe = self._write_json_meta_data(filtered_on_caption)

		for index, row in dataframe.iterrows():
			local_path = os.path.join(os.environ["OUT_PATH"], row['file_name'])
			shutil.copy2(local_path, training_image_path)

		shutil.copy2("metadata.jsonl", training_image_path)

		logging.info(f"Done moving files to training folder: Total Number of Images: {str(len(dataframe))}")

		return filtered_on_caption

	def _write_json_meta_data(self, all_current_images: list[dict]):
		"""
			# {"file_name": "0001.png", "text": "This is a golden retriever playing with a ball"}
			# {"file_name": "0002.png", "text": "A german shepherd"}
			# {"file_name": "0003.png", "text": "One chihuahua"}
		"""
		# Filter and unsure the other process found the captions
		all_current_images: list[dict] = [item for item in all_current_images if item.get('caption') is not None]

		logging.info(f"Total Raw Images: {len(all_current_images)}")
		present_images = []
		for image in all_current_images:
			"""
			{
			  "PartitionKey": "training",
			  "RowKey": "1000d16",
			  "image": "D:\\workspaces\\General\\scripts\\images\\GgFEagO.jpg",
			  "text": "Thoughts about my NYE party outfit?",
			  "id": "1000d16",
			  "author": "princessxo699",
			  "url": "https://i.imgur.com/GgFEagO.jpg",
			  "flair": "Outfit of the Day",
			  "permalink": "/r/SFWNextDoorGirls/comments/1000d16/thoughts_about_my_nye_party_outfit/",
			  "hash": "9951b4f82caeb8ba2bd9f79f8d422450"
			}
			"""

			if not os.path.exists(image.get('image')):
				logging.info(f"File does not exist, removing from list: {image.get('image')}")
			else:
				present_images.append(image)

		logging.info(f"Filtered Images: {len(present_images)}")

		data_frame = pandas.DataFrame(present_images,
									  columns=['image', 'text', 'id', 'author', 'url', 'flair', 'permalink', 'hash', 'caption'])

		# extract the file name from the image path
		file_name = data_frame['image'].map(lambda x: os.path.split(x)[-1])

		# extract the text from the data frame
		text = data_frame['text']
		caption = data_frame['caption']

		# create a new data frame with the file name and text
		filtered_frame = pandas.DataFrame({'file_name': file_name.values, 'text': text.values})

		alternate_frame = pandas.DataFrame({'file_name': file_name.values, 'text': caption.values})

		all_frames = pandas.concat([filtered_frame, alternate_frame])

		# write the data frame to a json lines file
		filtered_frame_json_lines = filtered_frame.to_json(orient='records', lines=True)
		alternate_frame_json_lines = alternate_frame.to_json(orient='records', lines=True)

		# write the json lines to a file
		with open('metadata.jsonl', 'w', encoding='utf-8') as f:
			f.write(filtered_frame_json_lines)
			f.write(alternate_frame_json_lines)

		return all_frames

	def move_training_to_cloud(self):
		logging.info("===Uploading training files to cloud===")
		training_image_path = os.environ["LOCAL_TRAINING_IMAGES"]
		for file in os.listdir():
			local_path = os.path.join(training_image_path, file)
			with open(local_path, "rb") as f:
				image_data = f.read()
				logging.info(f"Uploading: {file}")
				BlobAdapter("user_images").upload_blob(image_data, file)
		logging.info("===Done uploading training files to cloud===")
