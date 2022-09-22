# PhD Template

WIP

Available Options:
 - Language: English, Greek
 - Phase: Proposal, Report, Thesis
 - Status: Final, Draft

These options can be set in [./main.tex](./main.tex)

Based on the options above, one can use the [./tools/run.py](./tools/run.py) script to build the `main.tex` file.
Example generated file: [./PhD - Jane Doe - Thesis - Draft.pdf](./PhD%20-%20Jane%20Doe%20-%20Thesis%20-%20Draft.pdf)

Output of `python3 tools/run.py --build --help` :

```text
usage:  [-h] [--file FILE] [--build-dir BUILD_DIR] [--output-dir OUTPUT_DIR]
        [--phase {proposal,report,thesis,detect,all} [{proposal,report,thesis,detect,all} ...]]
        [--language {english,greek,detect,all} [{english,greek,detect,all} ...]]
        [--status {draft,final,detect,all} [{draft,final,detect,all} ...]]
        [--all] [--docker]

options:
  -h, --help            show this help message and exit
  --file FILE           Path to the main .tex file.
                        Default: ./main.tex
  --build-dir BUILD_DIR
                        Output directory.
                        Default: ./build
  --output-dir OUTPUT_DIR
                        Output directory.
                        Default: ./dist
  --phase {proposal,report,thesis,detect,all} [{proposal,report,thesis,detect,all} ...]
                        Phase(s) to use.
                        Available phases: proposal | report | thesis | detect | all.
                        Default: detect from tex file.
  --language {english,greek,detect,all} [{english,greek,detect,all} ...]
                        Language(s) to use.
                        Available languages: english | greek | detect | all.
                        Default: detect from tex file.
  --status {draft,final,detect,all} [{draft,final,detect,all} ...]
                        Status(es) to use.
                        Available statuses: draft | final | detect | all.
                        Default: detect from tex file.
  --all                 Alias for: --phase all --language all --status all. Overrides existing --phase --language --status arguments if any.
  --docker              Use docker image (texlive/texlive:latest) instead of local texlive (xelatex, biber).
```
