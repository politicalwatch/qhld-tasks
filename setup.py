from setuptools import setup, find_packages

setup(
    name="tipi-tasks",
    version="1.0.0",
    description="TIPI Tasks",
    url="https://github.com/politicalwatch/tipi-tasks",
    author="danigm",
    packages=find_packages(),
    install_requires=[
        "tipi-data @ git+https://github.com/politicalwatch/tipi-data.git",
        "celery[redis]==5.4.0",
        "certifi==2024.8.30",
        "chardet==5.2.0",
        "idna==3.10",
        "jinja2>=3.1.0",
        "markupsafe==3.0.2",
        "mongoengine==0.29.1",
        "pymongo==4.10.1",
        "regex==2024.11.6",
        "pytz==2024.2",
        "requests==2.32.3",
        "six==1.16.0",
        "sparkpost==1.3.10",
        "urllib3==2.6.3",
    ],
)
