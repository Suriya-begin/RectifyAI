RectifyAI

Intelligent OCR & LLM-Assisted Image Text Correction

RectifyAI is an end-to-end system that automatically detects and corrects spelling mistakes in AI/LLM-generated images.
It combines OCR, LLM-based contextual correction, and pixel-accurate image reconstruction, delivering a clean and corrected version of the original image while preserving layout and styling.

🚀 Key Features

📸 OCR-based text extraction from images

🧠 Context-aware spelling correction using Large Language Models

🧩 Rule-based fallback system when LLM is unavailable

🎨 Line-aware image reconstruction (font style, size, color preserved)

🌐 React frontend for interaction and visualization

🔄 End-to-end pipeline: Image → Corrected Image

🏗️ Project Architecture
RectifyAI/
│
├── backend/
│   ├── gemini_rectify.py          # Core OCR + LLM correction pipeline
│   ├── .env                       # API keys (not committed)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PremiumChat.jsx
│   │   │   ├── ChatWrapper.jsx
│   │   ├── styles/
│   │   │   ├── premiumchat.css
│   │   ├── App.jsx
│   │   ├── main.jsx
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── README.md


The React app handles UI and interaction, while the Python backend performs OCR, correction, and image reconstruction.

🧠 How RectifyAI Works (Pipeline)

OCR Extraction

Uses EasyOCR to extract text and bounding boxes from the image.

Stores extracted words and positions as JSON.

Intelligent Text Correction

Sends OCR output to an LLM (via Groq API).

Fixes spelling mistakes using surrounding context.

Falls back to a rule-based correction engine if the LLM fails.

Line-Aware Style Analysis

Groups words into lines.

Detects font size, boldness, text color, and background color.

Image Redrawing

Clears incorrect text regions.

Redraws corrected text pixel-accurately using PIL.

Preserves the original image layout and visual style.

Output

Generates a corrected image with accurate spelling.

🛠️ Tech Stack
🔹 Backend (AI & Image Processing)

Python

EasyOCR – text extraction

OpenCV – image processing

Pillow (PIL) – text redrawing

NumPy

Groq API – LLM inference (LLaMA-3.x)

dotenv – environment management

🔹 Frontend (UI)

React.js

Vite

JavaScript (ES6+)

CSS

Component-based architecture

🔹 AI / LLM

Large Language Models (LLaMA family)

Context-aware spelling correction

Rule-based fallback logic

⚙️ Setup Instructions
1️⃣ Clone the Repository
git clone https://github.com/your-username/RectifyAI.git
cd RectifyAI

2️⃣ Backend Setup (Python)
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux / macOS

pip install -r requirements.txt


Create a .env file:

GROQ_API_KEY=your_api_key_here


Update input/output paths in gemini_rectify.py if needed:

IMG_PATH = "path_to_input_image.png"
OUT_PATH = "path_to_output_image.png"


Run the pipeline:

python gemini_rectify.py

3️⃣ Frontend Setup (React)
cd frontend
npm install
npm run dev


The app will be available at:

http://localhost:5173

📸 Example Use Case

Input:
An AI-generated architecture diagram with spelling mistakes like:

“Positonial”

“Transfomer Blocks”

“LM Head”

Output:
A visually identical image with corrected text:

“Positional”

“Transformer Blocks”

“LLM Head”

🎯 Use Cases

Fixing spelling errors in LLM-generated diagrams

Cleaning AI-generated educational content

Pre-processing images for documentation and presentations

OCR post-processing pipelines

🔐 Notes

API keys are never committed

Supports both LLM-based and offline rule-based correction

Designed to be extensible (multi-language OCR, more models)

👨‍💻 Author

Suriya K S

GitHub: https://github.com/Suriya-begin

LinkedIn: https://www.linkedin.com/in/suriya-k-s-40a3b1351

📄 License

This project is licensed for educational and research use.
