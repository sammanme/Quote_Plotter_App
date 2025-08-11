Quote Plotter App is a full-stack web application built with FastAPI (backend) and React (frontend) to visualize financial market quotes. It allows users to compare historical and active bid and ask prices from multiple brokers and symbols in interactive charts and tables.

Features Fetches and displays bid/ask prices from different brokers and symbols

Interpolates missing data for smooth chart plotting

Interactive Chart.js line charts with zoom, pan, and tooltip support

Tabular display of prices and spreads

Configurable time ranges and number of data points

Responsive and user-friendly interface

Installation 

1. Backend (FastAPI) Clone the repository:

bash Copy Edit git clone https://github.com/yourusername/quote_plotter_app.git cd quote_plotter_app/backend Create and activate a virtual environment:

bash Copy Edit python3 -m venv venv source venv/bin/activate # Linux/macOS venv\Scripts\activate # Windows Install dependencies:

bash Copy Edit pip install -r requirements.txt Run the FastAPI server:

bash Copy Edit uvicorn main:app --reload The backend will be available at http://localhost:8000.

2. Frontend (React) Navigate to the frontend directory:

bash Copy Edit cd ../frontend Install dependencies:

bash Copy Edit npm install Start the React development server:

bash Copy Edit npm start The frontend will be available at http://localhost:3000.

Usage Open the frontend app in your browser.

Select brokers and symbols for comparison from the dropdown menus.

Choose a time range and number of spread points to display.

View the interactive chart plotting bid and ask prices.

Review the corresponding table with price details and calculated spreads.

Use zoom and pan features on the chart to explore data.

Reset zoom with the provided button if needed.

Contributing Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

If you want me to customize it further or add specific details, just say!
