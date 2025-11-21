import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO

# --- HARDCODED CONFIGURATION ---
# ⚠️ KEEP THIS PRIVATE. Do not commit this file to public GitHub repos.
API_KEY = st.secrets["GEMINI_API_KEY"]
ESP_IP = st.secrets["ESP_IP"]

# Page Config
st.set_page_config(page_title="Smart Fridge AI", layout="centered")

st.title("🥦 Smart Fridge Assistant")
st.caption(f"Powered by ESP32-CAM ({ESP_IP}) & Gemini 1.5 Flash")

# --- 1. DEFINE THE SYSTEM PROMPT HERE ---
system_instruction = """
You are a Smart Assistant with a culinary focus on Nigerian Cuisine. 
Your goal is to analyze images and help the user.

Follow these guidelines:
1. **Inventory:** Identify the ingredients, leftovers, and drinks visible in the image.
2. **Recipe Suggestions:** Suggest meals that can be made with the visible ingredients. 
   - **CRITICAL:** Prioritize Nigerian dishes (e.g., Jollof Rice, Egusi Soup, Yam and Egg, Fried Rice, Moi Moi, etc.) whenever the ingredients allow. If no image is passed dont hallucinate ingredients.
3. **Drink Pairings:** If you see beverages (milk, juice, malt, yogurt, zobo), suggest pairing them with a solid meal. 
   - Example: If you see milk or a cold drink, suggest eating it with Rice and Stew or Jollof Rice.
4. **Tone:** Be helpful, concise, and friendly.
"""

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to get image from ESP32
def get_image_from_esp32(url):
    try:
        # Added timeout to prevent hanging if ESP is off
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return image
        else:
            st.error(f"Failed to connect to camera. Status Code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# Main Logic
if API_KEY:
    genai.configure(api_key=API_KEY)
    
    # --- 2. MODEL CONFIGURATION ---
    # Changed '2.5' to '1.5' as 2.5 is not a valid public model version yet.
    model = genai.GenerativeModel(
        'gemini-2.5-flash', 
        system_instruction=system_instruction
    )

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image" in message:
                st.image(message["image"], width=300)
            st.markdown(message["content"])

    # Chat Input
    prompt = st.chat_input("Ask your fridge something...")

    if prompt:
        # Add User message to UI
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Fetch Image from ESP32
        fridge_image = None
        with st.spinner("Looking inside the fridge..."):
            fridge_image = get_image_from_esp32(ESP_IP)

        # Prepare inputs
        if fridge_image:
            with st.chat_message("user"):
                 st.image(fridge_image, caption="Camera View", width=300)
            # Save image to history for display context
            st.session_state.messages.append({"role": "user", "content": "(Image attached)", "image": fridge_image})
            
            inputs = [prompt, fridge_image]
        else:
            # Fallback if camera fails: just send text
            st.warning("Could not capture image. Sending text only.")
            inputs = [prompt]

        # Send to Gemini
        with st.chat_message("assistant"):
            with st.spinner("Analyzing ingredients..."):
                try:
                    response = model.generate_content(inputs)
                    st.markdown(response.text)
                    
                    # Add response to history
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"AI Error: {e}")
else:
    st.warning("API Key not found. Please check your code.")