import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from models.tweet import Tweet
from services.sentiment.sentiment_interface import SentimentInterface


class RobertaSentiment(SentimentInterface):

    MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

    LABELS = (
        "Negative",
        "Neutral",
        "Positive"
    )

    _model = None
    _tokenizer = None

    def __init__(self):

        if RobertaSentiment._model is None:

            print("Loading sentiment model...")

            RobertaSentiment._tokenizer = AutoTokenizer.from_pretrained(
                RobertaSentiment.MODEL_NAME
            )

            RobertaSentiment._model = AutoModelForSequenceClassification.from_pretrained(
                RobertaSentiment.MODEL_NAME
            )

            RobertaSentiment._model.eval()

            print("Sentiment model loaded successfully!")

        self.tokenizer = RobertaSentiment._tokenizer
        self.model = RobertaSentiment._model

    def analyze(self, tweet: Tweet) -> tuple[str, float]:

        inputs = self.tokenizer(
            tweet.text,
            return_tensors="pt",
            truncation=True
        )

        with torch.no_grad():

            outputs = self.model(**inputs)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )[0]

        predicted_class = torch.argmax(probabilities).item()

        confidence = probabilities[predicted_class].item()

        return (
            RobertaSentiment.LABELS[predicted_class],
            confidence
        )