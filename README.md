# RAG-LLM (WIP)

RAG-AI is a local application that leverages **Retrieval-Augmented Generation (RAG)** techniques with a locally hosted Language Model (LLM) like `llamacpp` or `kobold`, all written in Python.

The goal is to augment local LLM capabilities by integrating external knowledge retrieval, enhancing the assistant's ability to generate contextually relevant responses.

## Features
- Locally hosted LLM support (`llamacpp`/`kobold`)
- Retrieval-augmented generation to enhance LLM outputs
- Designed with extensibility for hybrid or pure vector database integration

## Future Development
- Adding a **vector database** for hybrid search and pure vector-based retrieval, improving knowledge retrieval efficiency.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/RAG-AI.git
   ```
2. Create virtual environment:
   ```bash
   python -m venv venv
   source ./venv/bin/activate
   ```
3. Install dependencies (in future):
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the application locally:
```bash
python main.py
```

## Contributing
Feel free to open issues or submit pull requests to improve the project.

## License
This project is licensed under the [MIT License](LICENSE).
