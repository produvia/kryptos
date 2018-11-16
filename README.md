# Kryptos

## About

Kryptos AI is a virtual investment assistant that manages your cryptocurrency portfolio. To learn more, check out the [Kryptos Slide Deck](https://docs.google.com/presentation/d/1O3BQ6fS9SuokJud8TZ1XPXX5QbjefAEiXNR3cxJIJwE/view) and the [Kryptos White Paper](https://docs.google.com/document/d/1Um9yoosEj-oZdEF3yMK2pt5TI0O2aRYhgkC0XJf_BVo/view).


## Installation

To get the entire project up and running locally:


Clone the repo:
```bash
$ git clone https://github.com/produvia/kryptos.git
$ cd kryptos
```

Build the docker images
```bash
$ docker-compose build
```

## Running locally

```bash
$ docker-compose up
```

This will spin up a web, worker, ml, postgres, and redis container.

The web app will be accessible at http://0.0.0.0:8080

You can also view the RQ dashboard at http://0.0.0.0:8080/rq

Hitting Ctl-C will stop all the containers.
To prevent this and run the containers in the background:

``` bash
$ docker-compose up -d
```

You can then selectively view the logs of any of the containers

``` bash
$ docker-compose logs -f <web|worker|ml>
```


## Local Development

Once the containers are running, you can access the the shell of any of the containers, use the `exec` command


For instance, to run strategies from CLI:
```bash
$ docker-compose exec worker bash
```

This will provide a command prompt inside the worker container from which you can run the `strat` command

For example, to work on the ML service:
```bash
# start all containers w/o logging
$ docker-compose up -d

# enter the ml shell
$ docker-compose exec ml bash

# or enter the worker shell to run a strategy
$ docker-compose exec worker bash
```

Then to stream ML logs in a separate terminal
```bash
docker-compose logs -f ml
```

To stop all containers

``` bash
$ docker-compose stop
```

To stopa specific container

``` bash
$ docker-compose stop <web|worker|ml>
```





## Contributing

When contributing to the codebase, please follow the branching model described [here](https://nvie.com/posts/a-successful-git-branching-model/)

Essentially, the two main branches are

 - `master`: the main branch containing the latest stable code released to production
 - `develop`: the "Work in Progress" branch where all new changes are merged into

Then there are [feature branches](https://nvie.com/posts/a-successful-git-branching-model/#feature-branches). These are the branches where you will make most of your commits. They branch off of develop, and are merged back into develop when the feature is complete.

### Setting up the development envrionment

Remember to get the lastest changes

``` bash
$ git checkout develop
$ git pull
```

Then create your new feature branch

``` bash
$ git checkout -b feature/<YOUR_FEATURE_NAME>
```

To push your latest changes to the repo

``` bash
$ git push origin feature<YOUR_FEATURE_BRANCH>
```

When you are ready to merge your feature branch back into develop

1. Ensure you have pushed your latest changes to the origin feature/<FEATURE_BRANCH> branch
2. Submit a pull request to the `develop` branch



## Project Components

For more information, check out documentation for the different services:

- [core](core/README.md) - for strategy related logic
- [ml](ml/README.md) - for machine learning models
- [web](web/README.md) - for the Telegram bot and web frontend
