import logging

import torch
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTFeatureExtractor, GPT2TokenizerFast

logger = logging.getLogger(__name__)


class ImageCaption:
	"""

	"""

	def __init__(self):
		self.device = torch.device("cpu")
		self.model = VisionEncoderDecoderModel.from_pretrained("D:\\models\\image-caption-generator")
		self.feature_extractor = ViTFeatureExtractor.from_pretrained("D:\\models\\image-caption-generator")
		self.tokenizer = GPT2TokenizerFast.from_pretrained("D:\\models\\image-caption-generator\\tokenizer")

	def caption_image(self, image_path) -> str:
		"""

		:param image_path:
		:return:
		"""
		img = Image.open(image_path)
		if img.mode != 'RGB':
			img = img.convert(mode="RGB")

		pixel_values = self.feature_extractor(images=[img], return_tensors="pt").pixel_values
		pixel_values = pixel_values.to(self.device)

		max_length = 128
		num_beams = 4

		# get model prediction
		output_ids = self.model.generate(pixel_values, num_beams=num_beams, max_length=max_length)

		# decode the generated prediction
		predictions = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
		return predictions
