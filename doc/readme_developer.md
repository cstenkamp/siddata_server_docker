# Readme for developers

If you are developing for this project, there are a few things you should know and do additionally to set up this project correctly. Under the section **Contributing** you will find what you'll need to set up to contribute to this project, and under the section **Further code requirements and information**, you'll find some more necessary information.

## Contributing

To adhere to common coding standards, this project uses **linting pre-comming hooks**, **automated testing using continuous integration**, as well as other standards.

### Linting

*Linters* are static code-checkers, that run over all of your `.py`-files and check if they adhere to a certain style and do not contain easily detectable errors (like using variables before assigning them). Next to linters, there are also **code formatters**, which automatically convert the coding style of your code (so everything that is not changing the syntax of the code, like if you're using single quotes or double quotes) to a standard, such that it is easier to collaborate on a big project like this.

In this project, we are using **black** as code formatter (and linter) as well as **flake8** as linter. Both of these can be run at different moments of the development process, most importantly **before committing** and **after pushing**. If linters are run after pushing, they cannot change anything about your code, but only complain and mark your contribution as dirty. If they run before committing, they may forbid you to actually commit with the current style, enforcing their own style. In the former way they may be used as a **pre-commit-hook**, in the latter one they are part of a **CI/CD (Continouous Integration/Continuous Deployment) Pipeline**. It is useful to incorporate both, as it is unfortunately impossible to automatically enforce the use of pre-commit hooks, which means that as long as a contributer didn't install the hooks as below, the commits will not adhere to the style agreed upon by the dev team - which means the CI/CD Pipeline will fail to let the team know that something is wrong about the commits.

#### How to set up Linting Pre-Commit Hooks

If you want to contribute, you can still run everything inside the docker-container as explained in the `doc/install.md`. However, we are using `pre-commit` with linting hooks, such as `black` and `flake8`. To set these up for your local development environment, you need to install at least the `requirements-dev.txt` outside of any container (on your **host OS**). For that, you should do the following:

If you didn't set up a conda environment before, follow the *download/install conda* section of the `doc/install.md` and create a new environment using `conda create -n siddata_p3f python=3.9`. Afterwards and in any case, run the following:

```
conda activate siddata_p3f
pip install -r requirements-dev.txt
pre-commit install
```

**Note that if your code needs to be reformatted (which will most likely be the case) these pre-commit-hooks will change your files on commit. If there were any changes by these hooks, the actual commit will be blocked, such that you may have to commit the files a second time!** (and, if the hooks noticed errors that it cannot automatically fix, fix the broken files manually).

To run the linters manually, you can use the command
```
pre-commit run --all-files
```

#### Read more about the code style

The code automatically gets reformatted to **black** style, see https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html for more information about it. *Please do not change anything about black's config, as there is a reason it's called **uncompromising**.*


### CI/CD and automated testing

CI/CD stands for Continouous Integration/Continuous Deployment, and the exact distinction between these two is hard to specify. What's usually done in CI/CD is to automatically create containers from your code whenever you commit to your repository. These containers should contain the full source of your code, such that it can easily be deployed in its newest version using container-management systems like docker.

In our case we use CI/CD for automated testing: Whenever you commit your code to the repository, the *workflow* under `.github/workflows` is automatically executed and creates a container. While this container is not pushed to any container-repository, it is used to **test the code** and create a report if the tests failed or passed. As explained in the section above, one part of this testing is **linting**. If you used the pre-commit hooks, the linting-tests should pass without problems, and if they fail please make sure to re-run `pre-commit run --all-files`.

The other simple test that is performed automatically is a so-called **smoketest**. This test just tries to spin up the Django-Environment using `manage.py runserver` inside the specified container and checks if it doesn't die. If it doesn't, it additionally looks at the health-check at `localhost:8000/health_check/`, to see if there are any problems with migrations and the like. If you don't see a green tick a few minutes after your commit, please make sure to check under the **Actions** Tab at https://github.com/virtUOS/siddata_server/actions to see what went wrong with your commit and fix it.


## Further code requirements and information

### Settings

Settings can be found under `src/settings/`. Note that there are multiple files, among others `settings_base.py`, `development.py`, `cd_autotest.py` and `development.py`. So then, how precisely do these work?

Most important is the `settings_base.py` file. This contains **all of the settings that must be equal for both production and development**. All other files in the `settings`-directory **import all settings from the `settings_base.py` and overwrite what the want to be different**.

If you are executing Django, for example by calling `manage.py runserver`, you can specify which settings-file you want to feed to the code using the environment-variable `DJANGO_SETTINGS_MODULE`. This is common practice for Django and really useful, because there are often settings that are supposed to be different for production and development (eg. the setting `DEBUG` should basically never be `True` for production, but always for development). To save oursaves the pain of writing those settings that are equal in both prod and dev (like eg. the language code of our project), we're simply using one file that contains all of these "global" settings, and then "inherit" these settings for different situations in which we want to use the code (namely production, development and automated testing in a ci/cd pipeline).

This also means that if you are contributing and want to **add** a setting, you got to think about if there is any reason (eg. security or differences when running multithreaded) why your setting should be different in production and development, and if so put it (all of!) the respective files. If it doesn't matter (almost all other cases), you can just add your setting to `settings_base.py`... But please **keep in mind that all of these files are part of the repository and should not contain sensitive information**, like any passwords!

So how do you incorporate passwords, then? Please, pretty please, use **Environment-Files** for this. Environment-files are simple textual files ending in `.env`, that simply contain lines of key-value-pairs (`KEY=VALUE`). You can simply use the python-library [python-dotenv](https://pypi.org/project/python-dotenv/) to load these environment-files, or use Pycharm, or docker. Once you read these files in your code, you can just use `os.getenv("KEY")` to read their contents, and that can even be done in the settings-files.

### Misc

#### Importing files

* Every `import` of project-files must start after `src`, eg. `from apps.backend.utils.log_utils import logger`.
    * For everything to work nicely in Pycharm, right-click on the `src`-dir and select "mark as -> sources root", such that you can use all files and import them correctly
* If you import settings, always import them as `from django.conf import settings` ! That way it is mades sure that even if you overwrite the `DJANGO_SETTINGS_MODULE`-env-variable you select the settings correctly!

#### Testing

* *TODO*: What do you need to run (tests) in order to know you set up everything completely and correctly
