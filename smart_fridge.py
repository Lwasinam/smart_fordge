# import streamlit as st
# import google.generativeai as genai
# from PIL import Image
# import requests
# from io import BytesIO
# import os

# # Page Config
# st.set_page_config(page_title="Smart Fridge AI", layout="centered")

# st.title("🥦 Smart Fridge Assistant")
# st.caption("Powered by ESP32-CAM & Gemini 1.5 Flash")

# # Sidebar for Setup
# with st.sidebar:
#     st.header("Setup")
#     api_key = st.text_input("Gemini API Key", type="password")
#     esp_ip = st.text_input("ESP32 Camera URL", value="http://192.168.1.XXX/capture")
#     st.info("Upload the code to your ESP32 and copy the IP address from the Serial Monitor.")

# # Initialize Chat History
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Function to get image from ESP32
# def get_image_from_esp32(url):
#     try:
#         response = requests.get(url, timeout=5)
#         if response.status_code == 200:
#             image = Image.open(BytesIO(response.content))
#             return image
#         else:
#             st.error("Failed to connect to camera.")
#             return None
#     except Exception as e:
#         st.error(f"Connection Error: {e}")
#         return None

# # Main Logic
# if api_key:
#     genai.configure(api_key=api_key)
#     model = genai.GenerativeModel('gemini-2.5-flash')

#     # Display chat history
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             if "image" in message:
#                 st.image(message["image"], width=300)
#             st.markdown(message["content"])

#     # Chat Input
#     prompt = st.chat_input("Ask your fridge something...")

#     if prompt:
#         # 1. Add User message to UI
#         with st.chat_message("user"):
#             st.markdown(prompt)
#         st.session_state.messages.append({"role": "user", "content": prompt})

#         # 2. Fetch Image from ESP32
#         with st.spinner("Looking inside the fridge..."):
#             # NOTE: In a real 'chat' flow, we might not take a photo every time,
#             # but for a smart fridge, context is usually visual.
#             fridge_image = get_image_from_esp32(esp_ip)

#         if fridge_image:
#             with st.chat_message("user"):
#                  st.image(fridge_image, caption="Camera View", width=300)
#             st.session_state.messages.append({"role": "user", "content": "(Image attached)", "image": fridge_image})
            
#             # 3. Send to Gemini
#             with st.chat_message("assistant"):
#                 with st.spinner("Analyzing ingredients..."):
#                     try:
#                         # Create prompt with image
#                         response = model.generate_content([prompt, fridge_image])
#                         st.markdown(response.text)
                        
#                         # Add response to history
#                         st.session_state.messages.append({"role": "assistant", "content": response.text})
#                     except Exception as e:
#                         st.error(f"AI Error: {e}")
# else:
#     st.warning("Please enter your Gemini API Key in the sidebar to start.")

import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO

# Page Config
st.set_page_config(page_title="Smart Fridge AI", layout="centered")

st.title("🥦 Smart Fridge Assistant")
st.caption("Powered by ESP32-CAM & Gemini 1.5 Flash")

# --- 1. DEFINE THE SYSTEM PROMPT HERE ---
system_instruction = """
You are a Smart Assistant with a culinary focus on Nigerian Cuisine. 
Your goal is to analyze images and help the user.

Follow these guidelines:
1. **Inventory:** Identify the ingredients, leftovers, and drinks visible in the image.
2. **Recipe Suggestions:** Suggest meals that can be made with the visible ingredients. 
   - **CRITICAL:** Prioritize Nigerian dishes (e.g., Jollof Rice, Egusi Soup, Yam and Egg, Fried Rice, Moi Moi, etc.) whenever the ingredients allow.
3. **Drink Pairings:** If you see beverages (milk, juice, malt, yogurt, zobo), suggest pairing them with a solid meal. 
   - Example: If you see milk or a cold drink, suggest eating it with Rice and Stew or Jollof Rice.
4. **Tone:** Be helpful, concise, and friendly.
"""

# Sidebar for Setup
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Gemini API Key", type="password")
    api_key  = "AIzaSyCN405y-JUyKB60FuOlyCaGnRmUOfmUs6g"
    # Default IP placeholder
    esp_ip = st.text_input("ESP32 Camera URL", value="http://192.168.1.XXX/capture")
    esp_ip = "http://10.15.72.125/capture"
    st.info("Upload the code to your ESP32 and copy the IP address from the Serial Monitor.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to get image from ESP32
def get_image_from_esp32(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return image
        else:
            st.error("Failed to connect to camera.")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# Main Logic
if api_key:
    genai.configure(api_key=api_key)
    
    # --- 2. PASS THE SYSTEM INSTRUCTION TO THE MODEL ---
    # Note: Use 'gemini-1.5-flash' (Standard model). '2.5' is not currently a standard public endpoint.
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
            fridge_image = get_image_from_esp32(esp_ip)

        # Even if image fails, we try to send text, but usually we want the image
        if fridge_image:
            with st.chat_message("user"):
                 st.image(fridge_image, caption="Camera View", width=300)
            # Save image to history for display context
            st.session_state.messages.append({"role": "user", "content": "(Image attached)", "image": fridge_image})
            
            inputs = [prompt, fridge_image]
        else:
            # Fallback if camera fails: just send text
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
    st.warning("Please enter your Gemini API Key in the sidebar to start.")