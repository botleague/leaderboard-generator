#### Requires

Python 3.7+

#### Install

```
pip install -e .
```

#### To run site locally

```
PORT=8889 python bin/serve.py
```

#### To automatically generate site when editing HTML/CSS/JS

```
python bin/autogen.py
```


#### Deployment setup

gcloud config set compute/zone [vm-zone]
gcloud config set project [vm-project-id]


#### Deploy, Test, SSH

[Makefile](Makefile)
