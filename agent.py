import streamlit as st
import os
import zipfile
import io
from langchain_google_genai import ChatGoogleGenerativeAI
from graphviz import Digraph
from PIL import Image
import base64

# Initialize Streamlit app
st.set_page_config(page_title="Website Generator AI", layout="wide")
st.title("Website Generator with AI Agents")
st.write("Enter a description of the website you want to create, configure the Gemini API settings, and generate HTML, CSS, and JS files.")

# Sidebar for API key and model settings
with st.sidebar:
    st.header("Gemini API Configuration")
    api_key = st.text_input("Enter your Google Gemini API Key", type="password")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=5000, value=1000, step=100)

# Main input area
user_input = st.text_area("Website Description", placeholder="e.g., Create a simple portfolio website with a navigation bar, about section, and contact form.", height=150)
generate_button = st.button("Generate Website")

# Initialize session state for storing results
if "results" not in st.session_state:
    st.session_state.results = None

# Function to validate inputs
def validate_inputs():
    if not api_key:
        st.error("Please enter a valid Gemini API key.")
        return False
    if not user_input.strip():
        st.error("Please provide a website description.")
        return False
    return True

# Define agent functions
def html_agent(user_input: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )
    prompt = f"Generate HTML code for a website based on this description: {user_input}. Return only the HTML code, no explanations."
    html_code = llm.invoke(prompt).content
    return html_code

def css_agent(html_code: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )
    prompt = f"Generate CSS code to style the following HTML for a website: {html_code}. Return only the CSS code, no explanations."
    css_code = llm.invoke(prompt).content
    return css_code

def js_agent(html_code: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )
    prompt = f"Generate JavaScript code to add interactivity to the following HTML: {html_code}. Return only the JS code, no explanations."
    js_code = llm.invoke(prompt).content
    return js_code

def file_agent(html_code: str, css_code: str, js_code: str) -> tuple[bytes, str]:
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("website_folder/index.html", html_code)
        zip_file.writestr("website_folder/styles.css", css_code)
        zip_file.writestr("website_folder/script.js", js_code)
    
    zip_buffer.seek(0)
    zip_data = zip_buffer.read()

    # Generate Graphviz dot file for file structure
    dot = Digraph(comment="Website File Structure")
    dot.node("website_folder", "website_folder")
    dot.node("index_html", "index.html")
    dot.node("styles_css", "styles.css")
    dot.node("script_js", "script.js")
    dot.edges([("website_folder", "index_html"), ("website_folder", "styles_css"), ("website_folder", "script_js")])
    graph_dot = dot.source

    return zip_data, graph_dot

# Run the agents when the button is clicked
if generate_button and validate_inputs():
    with st.spinner("Generating website files..."):
        try:
            # Execute agents sequentially
            html_code = html_agent(user_input)
            css_code = css_agent(html_code)
            js_code = js_agent(html_code)
            zip_file, graph_dot = file_agent(html_code, css_code, js_code)

            # Store results in session state
            st.session_state.results = {
                "html_code": html_code,
                "css_code": css_code,
                "js_code": js_code,
                "zip_file": zip_file,
                "graph_dot": graph_dot
            }
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display results if available
if st.session_state.results:
    results = st.session_state.results

    # Display generated code
    st.header("Generated Code")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("HTML (index.html)")
        st.code(results["html_code"], language="html")
    
    with col2:
        st.subheader("CSS (styles.css)")
        st.code(results["css_code"], language="css")
    
    with col3:
        st.subheader("JavaScript (script.js)")
        st.code(results["js_code"], language="javascript")

    # Display file structure graph
    st.header("File Structure")
    try:
        dot = Digraph()
        dot.body.append(results["graph_dot"])
        dot.render("file_structure", format="png", cleanup=True)
        st.image("file_structure.png", caption="Website File Structure")
    except Exception as e:
        st.warning(f"Could not render file structure graph: {str(e)}")
        st.code(results["graph_dot"], language="dot")

    # Provide download button for zip file
    st.header("Download Website Files")
    st.download_button(
        label="Download Website Files (ZIP)",
        data=results["zip_file"],
        file_name="website_files.zip",
        mime="application/zip"
    )