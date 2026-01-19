import torch
import torch.nn as nn
from torchvision.models import resnet50
from torchvision import transforms
from PIL import Image
from io import BytesIO
import requests

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
model = resnet50(weights=None)
model.fc = nn.Linear(model.fc.in_features, 2)

model.load_state_dict(
    torch.load("resnet50_nsfw_finetuned.pt", map_location=device)
)
model.to(device)
model.eval()

# Image transform (same as training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def predict_pil_image(image, threshold=0.8):
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        probs = torch.softmax(outputs, dim=1)

    nsfw_prob = probs[0][0].item()  # class 0
    sfw_prob = probs[0][1].item()  # class 1

    if nsfw_prob >= threshold:
        prediction = "NSFW"
        confidence = nsfw_prob
    else:
        prediction = "SFW"
        confidence = sfw_prob

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "sfw_confidence": round(sfw_prob, 4),
        "nsfw_confidence": round(nsfw_prob, 4)
    }


def predict_from_url(image_url, threshold=0.8):
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()

    image = Image.open(BytesIO(response.content)).convert("RGB")
    return predict_pil_image(image, threshold)
