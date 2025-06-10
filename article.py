import streamlit as st
import google.generativeai as genai
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# --- 0. API Key Configuration (INSECURE - Use Secrets in Production) ---
# Replace 'YOUR_GEMINI_API_KEY' with your actual Gemini API key
# WARNING: HARDCODING API KEYS IS A SECURITY RISK!
# Use Streamlit Secrets (.streamlit/secrets.toml) for production.
# Example for secrets.toml: GEMINI_API_KEY="your_key_here"
# Then access with st.secrets["GEMINI_API_KEY"]
GEMINI_API_KEY = "AIzaSyDyuQQiJyDfCpayS7-sLPHZKtnAAZQRWEU"

# Configure the generative AI model
genai.configure(api_key="AIzaSyDyuQQiJyDfCpayS7-sLPHZKtnAAZQRWEU")


# --- 1. Helper Functions ---

def generate_article_text(prompt_text, article_format, tone):
    """Generates article text using Gemini API based on prompt, format, and tone."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # Or another suitable Gemini model

        # Construct the prompt for the model
        # This prompt needs to be clear and guide the model effectively
        prompt = f"""
        Generate an article based on the following core text or idea.
        Format: {article_format}
        Tone: {tone}

        Core Text/Idea:
        {prompt_text}

        Please write the article now:
        """

        response = model.generate_content(prompt)

        # Access the generated text
        # Check if content was generated successfully
        if response and response.candidates:
             # Some models might return parts, join them
            generated_text = "".join([part.text for part in response.candidates[0].content.parts])
            return generated_text
        else:
            st.error("Failed to generate content. Response or candidates were empty.")
            st.write("Response:", response) # Optional: for debugging
            return None

    except Exception as e:
        st.error(f"An error occurred during generation: {e}")
        return None

def create_pdf(text):
    """Creates a PDF from the given text in memory."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize=(8.5 * inch, 11 * inch),
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = []

    # Use Paragraph to handle text wrapping
    # Split text into paragraphs (assuming double newline separates paragraphs)
    paragraphs = text.split('\n\n')
    for para_text in paragraphs:
        # Handle single newlines within potential paragraphs more gracefully if needed
        para_text = para_text.replace('\n', '<br/>') # Simple handling for single newlines
        story.append(Paragraph(para_text, styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal'])) # Add spacing between paragraphs

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- 2. Streamlit App Layout ---

st.set_page_config(page_title="AI Article Generator", layout="wide")

st.title("📝 AI Article Generator")

st.markdown("""
Generate articles based on your input text, choosing the format and tone.
Powered by Google Gemini.
""")

# --- 3. User Input Section ---

st.header("Input")

# Use Streamlit's session state to preserve input across reruns (especially for regenerate)
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""
if 'format' not in st.session_state:
    st.session_state.format = "Standard Article"
if 'tone' not in st.session_state:
    st.session_state.tone = "Neutral"
if 'generated_article' not in st.session_state:
    st.session_state.generated_article = None


input_text = st.text_area(
    "Enter your core text or idea here:",
    value=st.session_state.input_text,
    height=200,
    help="Provide the main information or concept for the article."
)
# Update session state whenever the text area changes
st.session_state.input_text = input_text


# --- 4. Format and Tone Selection ---

st.header("Options")

col1, col2 = st.columns(2)

with col1:
    article_format = st.selectbox(
        "Select Article Format:",
        ["Standard Article", "Blog Post", "Press Release", "Short Summary", "Detailed Report Section"],
        index=["Standard Article", "Blog Post", "Press Release", "Short Summary", "Detailed Report Section"].index(st.session_state.format),
        help="Choose the structure and style of the output.",
        key='format_select' # Use a key to ensure session state updates correctly
    )
    st.session_state.format = article_format # Update session state

with col2:
    tone = st.selectbox(
        "Select Tone:",
        ["Neutral", "Formal", "Informal", "Enthusiastic", "Critical", "Humorous"],
        index=["Neutral", "Formal", "Informal", "Enthusiastic", "Critical", "Humorous"].index(st.session_state.tone),
        help="Choose the emotional or stylistic tone of the writing.",
        key='tone_select' # Use a key
    )
    st.session_state.tone = tone # Update session state

# --- 5. Generation Buttons ---

# Create a container for buttons to manage layout
button_container = st.container()

with button_container:
    col_gen, col_regen, col_spacer = st.columns([1, 1, 3]) # Use spacer to push buttons left

    with col_gen:
        generate_button = st.button("Generate Article", use_container_width=True)

    with col_regen:
        # Only show regenerate if an article has been generated previously
        if st.session_state.generated_article:
             regenerate_button = st.button("Regenerate Article", use_container_width=True)
        else:
             # Use a placeholder if regenerate button is not shown
             regenerate_button = False # Ensure it's False if button not rendered

# --- 6. Article Generation Logic ---

# Check which button was clicked or if regeneration is triggered
if generate_button or regenerate_button:
    if not st.session_state.input_text:
        st.warning("Please enter some text or idea to generate an article.")
    else:
        with st.spinner("Generating article... Please wait."):
            # Pass values from session state (they are already updated by text_area and selectboxes)
            generated_article = generate_article_text(
                st.session_state.input_text,
                st.session_state.format,
                st.session_state.tone
            )

            if generated_article:
                st.session_state.generated_article = generated_article # Store in session state
                st.success("Article generated successfully!")
            else:
                 # Error message is handled inside generate_article_text
                 st.session_state.generated_article = None # Reset if generation failed

# --- 7. Display Generated Article ---

st.header("Generated Article")

if st.session_state.generated_article:
    # Display the generated article
    st.markdown(st.session_state.generated_article) # Use markdown for better formatting

    # --- 8. Download PDF Button ---
    st.header("Download")
    pdf_buffer = create_pdf(st.session_state.generated_article)
    st.download_button(
        label="Download Article as PDF",
        data=pdf_buffer,
        file_name="generated_article.pdf",
        mime="application/pdf",
        help="Download the current generated article as a PDF file."
    )
else:
    st.info("The generated article will appear here after you click 'Generate Article'.")

# --- 9. Footer ---
st.markdown("---")
st.markdown("<sub>*This application uses the Google Gemini API.*</sub>", unsafe_allow_html=True)
