import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

# Load FinBERT
# This model outputs logits for [Positive, Negative, Neutral]
MODEL_NAME = "ProsusAI/finbert"

tokenizer = None
model = None

def load_model():
    global tokenizer, model
    if tokenizer is None or model is None:
        logger.info("Loading FinBERT model...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        model.eval()

def analyze_sentiment(text: str) -> float:
    """
    Analyzes text and returns a net sentiment score between -1.0 and 1.0.
    Positive -> closer to 1.0
    Negative -> closer to -1.0
    Neutral  -> closer to 0.0
    """
    if not text:
        return 0.0
        
    load_model()
    
    # FinBERT max length is 512 tokens. We chunk the text.
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
        
    # FinBERT labels: 0=Positive, 1=Negative, 2=Neutral
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
    
    prob_pos = probabilities[0].item()
    prob_neg = probabilities[1].item()
    
    # Net sentiment score: positive probability - negative probability
    net_sentiment = prob_pos - prob_neg
    return net_sentiment
