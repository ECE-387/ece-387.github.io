# ECE387
ECE387 Course Web

### How to install required Python packages? 
- Open a terminal.
- Navigate to the root folder and find requirements.txt
- run `pip install -r requirements.txt` for Windows machines
- run `pip install -r requirements_linux.txt` for Linux machines
- I recommned using a virtual environment.

### How to build and publish?
- Run `sudo apt install ghp-import`
- Run the following under the `book` folder.
- Build: `jupyter-book build --all .`  
- Publish: `ghp-import -n -p -f _build/html` 

### Recommended extensions for vscode
- Python, Python Extension Pack
- Jupyter, MyST-Markdown

### Convert jupyter notebook to markdown
- jupytext https://jupytext.readthedocs.io/en/latest/using-cli.html
- install: pip install jupytext
- How to use: jupytext lab2.ipynb --to md

### To remove version constraints

To remove version constraints from a requirements.txt file (e.g., turning numpy==1.23.4 into numpy), you can use a simple shell command or Python script.
```bash
sed -E 's/[<=>~!]=?.*//' requirements.txt > requirements_no_versions.txt
```