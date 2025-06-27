<div id="top"></div>

<!-- PROJECT SHIELDS -->
<div align="center">

[![Contributors][contributors-shield]][contributors-url] [![Forks][forks-shield]][forks-url] [![Stargazers][stars-shield]][stars-url] [![Issues][issues-shield]][issues-url] [![License][license-shield]][license-url]

</div>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <!-- <a href="https://github.com/greydelta/orion-ai">
    <img src="./images/Logo.jpg" alt="Logo" width="621px" height="258px">
  </a> -->

<h3 align="center">OrionAI</h3>

  <p align="center">Agentic system for transforming source code into structured documentation<br />
    <a href="https://github.com/greydelta/orion-ai"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/greydelta/orion-ai">View Demo</a>
    ·
    <a href="https://github.com/greydelta/orion-ai/issues">Report Bug</a>
    ·
    <a href="https://github.com/greydelta/orion-ai/issues">Request Feature</a>
  </p>
</div>

<!-- ABOUT THE PROJECT -->

## About The Project

### Project Deliverables:

- Build an agentic LLM pipeline that converts source code and repositories into structured documentation and summaries

- Implement autonomous role-driven prompt orchestration (e.g., Software Engineer, Product Manager, Architect)

- Integrate validation and conditional reprocessing logic using LangGraph to ensure output quality

- Support multiple LLM backends (OpenAI, Gemini, Claude, Ollama) and allow for backend switching

- Automate common tasks such as:
  - Converting single files or entire repositories
  - Reviewing and validating model outputs
  - Summarizing functionality and generating user stories
  - Retrying failed generations or rerouting based on tool output

### Workflow

- Users initiate a conversion request with a file or repository input

- The system dynamically determines the appropriate roles and tool sequences to process the input

- Structured outputs are validated using Pydantic and further refined if necessary

- Final outputs can be summarized and exported as documentation or user stories

### System Flowchart:

<div align="center">

[![flowchart][media-flowchart]](#)

</div>

<!-- ### System snapshot(s):

<div align="center">

[![output-1][media-output1]](#) [![output-2][media-output2]](#) [![output-3][media-output3]](#) [![output-4][media-output4]](#)

</div>

<p align="right">(<a href="#top">back to top</a>)</p> -->

### Built With

### Front-End: ![Streamlit](https://img.shields.io/badge/streamlit-%23FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)

### Back-End: ![Python](https://img.shields.io/badge/python-%2314354C.svg?style=for-the-badge&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/fastapi-%2300C7B7.svg?style=for-the-badge&logo=fastapi&logoColor=white) ![LangChain](https://img.shields.io/badge/langchain-181717?style=for-the-badge&logo=langchain&logoColor=white) ![Supabase](https://img.shields.io/badge/supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [x] File & Repo ingestion
- [x] Role-based prompt pipeline (Engineer → PM → Architect)
- [x] Model-agnostic backend support (OpenAI, Gemini, Claude, Ollama)
- [x] Output validation (Pydantic-based schema enforcement)
- [x] Manual control over conversion and summarization
- [ ] Internal tool abstraction layer for LLM access
- [ ] Dynamic tool selection via LLM planning
- [ ] Basic agent execution (LangGraph integration for branching & retries)
  - [ ] Retry & fallback logic based on validation outcomes
- [ ] Goal-based instruction planning (agent decides workflow autonomously)
- [ ] Tokenization & context window optimization (e.g. chunking, pruning, compression)
- [ ] Memory/context retention across multi-file or multi-repo jobs
- [ ] Clarification handling & meta-cognition tools

> 🧠 OrionAI is currently operating as a structured, role-based pipeline. However, development is actively progressing toward an **agentic architecture**, where tools and functions are exposed to the LLM to enable autonomous reasoning and dynamic execution.

See the [open issues](https://github.com/greydelta/orion-ai/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

### Using [![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)](https://www.eclipse.org/ide/):

#### Prerequisites

1. Clone the repo into your local directory

#### Installation

- Ensure Python 3.10+, Node.js, and virtualenv are installed

#### Usage

1. Create a `.env` file and set variables

1. Ensure all environment variables for endpoints and API keys are set

   - Set `LOCAL_MCP_SERVER_URL` = `http://localhost:8081`
   - If using Ollama, set `OLLAMA_URL` & `OLLAMA_MODELS`
   - If using online models, set relevant `API_KEY_<your_model_of_choice>`
   - Set `DB_URL` connection string to database of choice

1. Enter virtualenv:

   ```bash
    python -m pipenv shell
   ```

1. Install dependencies:

   ```bash
    pip install -r requirements.txt
   ```

1. Run the MCP server:

   ```bash
    cd orion-ai
    uvicorn app.main:app --reload --port 8081
   ```

1. Run the Steamlit app:

   ```bash
    cd orion-ai
    streamlit run app.py
   ```

1. Navigate to `http://localhost:8501/` to access the app

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- LICENSE -->

## License

Distributed under the GNU AGPLv3 License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

<div align="center">
    <a href="https://discord.com/users/379539771837513729" target="_blank">
  <img src="https://img.shields.io/badge/discord:  @double.decompose-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white" alt=discord style="margin-bottom: 5px;"/>
  </a> <a href="mailto:dev.aw.qwe@gmail.com" target="_blank">
  <img src="https://img.shields.io/badge/gmail:  dev.aw.qwe@gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt=mail style="margin-bottom: 5px;" />
  </a>
</div>

<br />

Project Link: [https://github.com/greydelta/orion-ai](https://github.com/greydelta/orion-ai)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->

[contributors-shield]: https://img.shields.io/github/contributors/greydelta/orion-ai.svg?style=for-the-badge
[contributors-url]: https://github.com/greydelta/orion-ai/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/greydelta/orion-ai.svg?style=for-the-badge
[forks-url]: https://github.com/greydelta/orion-ai/network/members
[stars-shield]: https://img.shields.io/github/stars/greydelta/orion-ai.svg?style=for-the-badge
[stars-url]: https://github.com/greydelta/orion-ai/stargazers
[issues-shield]: https://img.shields.io/github/issues/greydelta/orion-ai.svg?style=for-the-badge
[issues-url]: https://github.com/greydelta/orion-ai/issues
[license-shield]: https://img.shields.io/github/license/greydelta/orion-ai.svg?style=for-the-badge
[license-url]: https://github.com/greydelta/orion-ai/blob/master/LICENSE.txt
[media-logo]: /images/Logo.jpg
[media-flowchart]: /readMeImages/flowchart.png

<!-- [media-output1]: /readMeImages/snapshot_1.png
[media-output2]: /readMeImages/snapshot_2.png
[media-output3]: /readMeImages/snapshot_3.png
[media-output4]: /readMeImages/snapshot_4.png -->
