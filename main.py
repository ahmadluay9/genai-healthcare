import base64, uvicorn, vertexai, requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Security, status, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2 import service_account
import google.auth

CREDENTIALS, _ = google.auth.default()

SECREETMANAGER_ID = "projects/664275974519/secrets/genai-medical"
SCREET_ENDPOINT_URL = f"https://secretmanager.googleapis.com/v1/{SECREETMANAGER_ID}/versions/1:access"
PROJECT_ID = "sismedika-his-130824"
LOCATION = "us-central1"

# Inisialisasi Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=CREDENTIALS)

try:
    # Mendapatkan token
    auth_req = google.auth.transport.requests.Request()
    CREDENTIALS.refresh(auth_req)
    bearer_token = CREDENTIALS.token

    # Mendapatkan API key
    response = requests.get(SCREET_ENDPOINT_URL, headers={"Authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"})
    response.raise_for_status()
    
    if response.status_code == 200:
        apiKey_google_encoded = response.json().get('payload', {}).get('data')
        if apiKey_google_encoded:
            apiKey_google = base64.b64decode(apiKey_google_encoded.encode('utf-8')).decode('utf-8')
        else:
            raise ValueError("API key not found in the response.")
    else:
        raise ValueError("Error retrieving API key.")
except (requests.exceptions.RequestException, ValueError) as e:
    error_message = f"Failed to retrieve token or API key: {e}"
    status_code = response.status_code if 'response' in locals() else 500
    raise HTTPException(status_code=status_code, detail={"error": error_message})

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Konfigurasi middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["POST"],  
    allow_headers=["Content-Type", "X-API-Key"],
)

# Model untuk respon ringkasan audio
class AudioSummaryResponse(BaseModel):
    content: str

# Fungsi untuk mendapatkan API key dari header
async def get_api_key(api_key_header: str = Security(APIKeyHeader(name="X-API-Key", auto_error=False))):
    if (api_key_header is None) or (api_key_header != apiKey_google):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")
    return api_key_header

# Fungsi untuk mendapatkan ringkasan dengan Gemini
def get_summarize_gemini(mp3_data: bytes, model_name: str):
    from vertexai.generative_models import GenerativeModel, Part, Tool
    import vertexai.preview.generative_models as generative_models

    system_prompt = """
    You are an Assistant Doctor specializing in Medical Health and you are at Hospital, tasked with summarizing the key points of conversations between patients and doctors and providing suggestions to the doctor regarding the possible disease the patient may be suffering from based on the symptoms discussed.
    Follow these steps to give your suggestions to the doctor:
    1. Summarize the conversation in bullet points.
    2. Based on the summarized points, provide a single diagnosis suggestion that has the highest likelihood and provide a scientific explanation about the disease.
    3. Identify suitable medications for each symptom and for the primary condition.

    Please focus on the primary symptoms, diagnosis, and recommended medications.
    Ensure that your suggestions are based solely on the summarized conversation and do not include any additional notes or disclaimers. Your response must be in Indonesian.
    If the conversation lacks sufficient detail for a meaningful summary, respond with:
    'Maaf, percakapannya tidak cukup untuk diringkas. Tolong berikan percakapan yang lebih panjang.'

    The response format that should be output:

    ## Ringkasan Gejala:
    * Symptom 1
    * Symptom 2
    * Symptom 3

    ## Diagnosis:
    Diagnosis

    ## Rekomendasi Obat:
    [Symptom or Diagnosis]:
    - Medication 1
    - Medication 2
    - Medication 3

    Content Restrictions:
    Do not include any notes or instructions about referring to a doctor or hospital for further diagnosis or treatment.
    """

    data = base64.b64encode(mp3_data).decode('utf-8')
    audio = Part.from_data(mime_type="audio/mpeg", data=data)

    generation_config = {
        "max_output_tokens": 512,
        "temperature": 0.0,
        "top_p": 1,
    }

    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    try:
        model = GenerativeModel(
            model_name,
            system_instruction=[system_prompt]
        )

        responses = model.generate_content(
            [audio, "Please summarize the conversation in this audio and provide the diagnosis and recommended medication"],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False
        )
    except Exception as e:
        raise RuntimeError(f"Failed to generate content: {str(e)}")

    return responses.text

# Endpoint untuk mendapatkan ringkasan audio
@app.post("/get_summarize_gemini", response_model=AudioSummaryResponse, dependencies=[Depends(get_api_key)])
async def summarize_audio_endpoint(file: UploadFile = File(...), model_name: str = "gemini-1.5-pro-001"):
    try:
        mp3_data = await file.read()
        summary = get_summarize_gemini(mp3_data, model_name)
        return AudioSummaryResponse(content=summary)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":