# Readme for developers


## Linting

We are using `pre-commit` with linting hooks, such as `black` and `flake8`. To set these up for your local development environment, you need to install at least the `requirements-dev.txt` outside of any container. For that, you should run

```
#If you haven't set up your environment before:
conda create -n siddata_p3f python=3.9
```
```
conda activate siddata_p3f
pip install -r requirements-dev.txt
pre-commit install
```
Note that if your code needs to be reformatted, these pre-commit-hooks may change your files on commit. If there
were any changes by these hooks, the actual commit will be blocked, such that you may have to commit the files a
second time.

### Code Style

* Code automatically gets reformatted to **black** style, see https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html



## Further code requirements

* Every import of project-files must start after `src`, eg. `from apps.backend.utils.log_utils import logger`.

## Misc

* For everything to work nicely in Pycharm, right-click on the `src`-dir and select "mark as -> sources"
* If you import settings, always import them as `from django.conf import settings`
