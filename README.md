# InternationAlly

[InternationAlly](https://github.com/Property-Pilot/Property-Pilot) is an AI-powered trusted international student advisor, helping students feel comfortable and confident in their new foreign environment.

## Overview

InternationAlly provides international students with a comprehensive platform to navigate the challenges of moving abroad. The application offers:

- **Housing Search**: Find suitable housing options tailored to international students' needs
- **Local Advice**: Discover essential services and popular destinations in your new location
- **International Student Guidance**: Get support on legal, cultural, and logistical matters
- **Interactive Map**: Visualize housing options and local amenities

## Features

- AI-powered chat interface with specialized agents for different domains
- User account creation and authentication
- Chat history saving and retrieval
- Interactive Google Maps integration
- Property search via Zillow API
- Retrieval-Augmented Generation (RAG) for accurate information

## Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **AI/ML**: LangChain, LangGraph, OpenAI, Google Gemini, Anthropic Claude
- **Vector Database**: ChromaDB
- **APIs**: Google Maps, Zillow

## Project Structure

```
InternationAlly-v2/
├── app/
│   ├── api/              # API routes and integrations
│   ├── components/       # Reusable UI components
│   ├── models/           # Database models
│   ├── pages/            # Page templates
│   ├── static/           # Static assets (CSS, JS, images)
│   └── utils/            # Utility functions
├── app.py                # Main application file
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── README.md             # Project documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Acknowledgements

InternationAlly was originally developed as a capstone project for the Applied Data Science Master's program at the University of Chicago by:

- Kshitiz Sahay
- Daichi Ishikawa
- Yijing Sun
- William DeForest

This version is a rebuild with enhanced features and improved architecture.
