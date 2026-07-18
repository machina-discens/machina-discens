# Machina-Discens
Machina Discens (Lat.) — Learning Machine (the machine that is learning as we speak).

In order to launch it from the command line or as a Python subprocess:
```bash
echo "Theodotos-Alexandreus: What have you learned, machine?" \
  | uvx machina-discens \
    --provider-api-key=sk-proj-... \
    --github-token=ghp_... 
```

Or, with a local pip installation:
```bash
pip install machina-discens
```
Set the environment variables:
```bash
export PROVIDER_API_KEY="sk-proj-..."
export GITHUB_TOKEN="ghp_..."
```
Then:
```bash
machina-discens multilogue.txt
```
Or:
```bash
machina-discens multilogue.txt > output.txt
```
Or:
```bash
machina-discens multilogue.txt > tmp && mv tmp multilogue.txt
```
Or:
```bash
cat multilogue.txt new_turn.txt | machina-discens
```
Or:
```bash
cat multilogue.txt new_turn.txt | machina-discens > tmp && mv tmp multilogue.txt
```
Or: 
```bash
(cat multilogue.txt; echo:"Theodotos: What do you think, Machina-Discens?") \
  | machina-discens
```
Or:
```bash
cat multilogue.txt new_turn.txt | machina-discens > tmp && mv tmp multilogue.txt
```
Or, if you have installed other machines:
```bash
cat multilogue.md | machina-discens \
  | summarizing-machine | judging-machine > summary_judgment.md
```

Or use it in your Python code:
```Python
# Python
import machina_discens
```
