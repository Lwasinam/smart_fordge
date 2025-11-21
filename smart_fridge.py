import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
from PIL import Image
import requests
from io import BytesIO
import time

# --- CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except FileNotFoundError:
    st.error("Secrets not found. Please check .streamlit/secrets.toml")
    st.stop()

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Page Config
st.set_page_config(page_title="Smart Fridge AI", layout="centered")

st.title("🥦 Smart Fridge Assistant")
st.caption("Powered by ESP32-CAM (Supabase Cloud) & Gemini 1.5 Flash")

# --- SYSTEM PROMPT ---
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

# Function to get image from Supabase Storage
def get_image_from_supabase():
    bucket_name = "fridge-images"
    file_name = "latest_snap.jpg"
    
    try:
        # 1. Get the public URL
        image_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        
        # 2. Cache Busting: Add a timestamp query param
        # This forces Streamlit to download the NEW image, not the old cached one.
        image_url_with_time = f"{image_url}?t={int(time.time())}"
        
        # 3. Download the image
        response = requests.get(image_url_with_time, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            st.warning(f"Could not find image in Supabase. (Status: {response.status_code})")
            return None
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

# Main Logic
if API_KEY:
    genai.configure(api_key=API_KEY)
    
    # --- MODEL CONFIGURATION ---
    # FIXED: Changed to 1.5-flash (2.5 does not exist yet)
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

        # Fetch Image from Supabase
        fridge_image = None
        with st.spinner("Checking cloud storage for latest photo..."):
            fridge_image = get_image_from_supabase()

        # Prepare inputs
        if fridge_image:
            with st.chat_message("user"):
                 st.image(fridge_image, caption="Latest Fridge View", width=300)
            
            # Save image to history
            st.session_state.messages.append({"role": "user", "content": "(Image attached)", "image": fridge_image})
            
            inputs = [prompt, fridge_image]
        else:
            st.warning("No image found. Using text only.")
            inputs = [prompt]

        # Send to Gemini
        with st.chat_message("assistant"):
            with st.spinner("Analyzing ingredients..."):
                try:
                    response = model.generate_content(inputs)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"AI Error: {e}")
else:
    st.warning("API Key not found. Please check your secrets.")