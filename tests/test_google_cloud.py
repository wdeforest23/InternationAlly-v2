import vertexai
from vertexai.preview.generative_models import GenerativeModel, ChatSession
import vertexai.preview.generative_models as generative_models
from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
import os

def test_google_cloud_setup():
    """Test Google Cloud credentials and Vertex AI setup"""
    try:
        # Load environment variables
        load_dotenv()
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not credentials_path:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")
        
        if not os.path.exists(credentials_path):
            raise Exception(f"Credentials file not found at: {credentials_path}")
            
        print(f"Using credentials from: {credentials_path}")
        
        # Configure safety settings
        safety_config = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.OFF,
            ),
        ]
        
        print("\n1. Testing Google Cloud initialization...")
        vertexai.init(project="internationally", location="us-central1")
        print("✓ Successfully initialized Google Cloud Platform")
        
        print("\n2. Testing Gemini model access...")
        model = GenerativeModel("gemini-2.0-flash-001", safety_settings=safety_config)
        chat = model.start_chat(response_validation=False)
        print("✓ Successfully accessed Gemini model and started chat")
        
        print("\n3. Testing model prediction...")
        response = chat.send_message(
            "What is the capital of France? Please answer in one word.",
            stream=True
        )
        text_response = []
        for chunk in response:
            if hasattr(chunk, 'text'):
                text_response.append(chunk.text)
        final_response = "".join(text_response)
        print(f"✓ Successfully received response: {final_response}")
        
        print("\n✓ All tests passed! Your Google Cloud setup is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Install the preview version of the library:")
        print("   pip install google-cloud-aiplatform[preview]")
        print("2. Make sure you have the latest generative AI library:")
        print("   pip install --upgrade google-generativeai")
        print("3. Check that your service account has the Vertex AI Service Agent role")
        return False

if __name__ == "__main__":
    test_google_cloud_setup() 